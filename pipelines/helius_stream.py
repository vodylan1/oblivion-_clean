"""
Minimal Helius WebSocket account-subscribe feed for Oblivion.

Subscribes to every pubkey in wallets/stealth_pool.json and
pushes raw payloads into an asyncio.Queue consumed by strategies.

A stub path is activated when HELIUS_API_KEY is *not* set so that
unit-tests / CI can import this module without needing live keys.
"""
from __future__ import annotations

import os
import json
import asyncio
import pathlib
import random
from typing import Final

import aiohttp
import backoff

# --------------------------------------------------------------------------- #
# ――― environment & stub fallback ―――
# --------------------------------------------------------------------------- #
API_KEY: Final[str] = os.getenv("HELIUS_API_KEY", "stub-key")

if API_KEY == "stub-key":
    # --------------------------------------------------------------------- #
    # CI / test path: expose the two helpers other modules expect and bail
    # --------------------------------------------------------------------- #
    def subscribe(*_a, **_k):  # noqa: D401,E501
        """No-op stub used in unit-tests."""
        raise RuntimeError("Helius stream is disabled in CI (no API key).")

    def get_cursor() -> str:  # noqa: D401
        """Return a fake cursor so callers have something deterministic."""
        return "0"

else:
    # --------------------------------------------------------------------- #
    # Real implementation (unchanged apart from using API_KEY)
    # --------------------------------------------------------------------- #
    STEALTH_JSON = pathlib.Path("wallets/stealth_pool.json")

    # tenant-specific URLs (your key lives on *.helius-rpc.com)
    WS_URL_V1 = f"wss://mainnet.helius-rpc.com/?api-key={API_KEY}"
    WS_URL_V0 = f"wss://atlas-mainnet.helius-rpc.com/?api-key={API_KEY}"

    # simple fan-out queue; strategies may read from this later
    helius_queue: asyncio.Queue[dict] = asyncio.Queue(maxsize=2048)

    # -------------------------------------------------------------------- #
    async def on_msg(payload: dict) -> None:
        """
        Async callback for every account notification.
        Currently just enqueues the raw payload; later we can pre-parse.
        """
        try:
            helius_queue.put_nowait(payload)
        except asyncio.QueueFull:
            # drop oldest to keep moving
            _ = await helius_queue.get()
            helius_queue.put_nowait(payload)

    # -------------------------------------------------------------------- #
    async def _connect_and_stream(ws_url: str) -> None:
        """Open WS, subscribe, pump messages until disconnect."""
        with STEALTH_JSON.open() as fh:
            accs = [w["pubkey"] for w in json.load(fh)["wallets"]]

        sub_msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "accountSubscribe",
            "params": [accs, {"encoding": "base64"}],
        }

        async with aiohttp.ClientSession() as sess, sess.ws_connect(
            ws_url, autoping=True, heartbeat=15
        ) as ws:
            await ws.send_json(sub_msg)
            print(f"[helius] subscribed to {len(accs)} accounts via {ws_url}")

            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    await on_msg(data)  # on_msg is async
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    raise msg.data

    # -------------------------------------------------------------------- #
    @backoff.on_exception(backoff.expo, Exception, max_time=3600, jitter=random.random)
    async def helius_stream_task() -> None:
        """
        Resilient wrapper: try V1, fall back to Atlas, auto-reconnect with
        exponential back-off (max 1 h) if either side drops.
        """
        try_order = [WS_URL_V1, WS_URL_V0]
        while True:
            for url in try_order:
                try:
                    await _connect_and_stream(url)
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    print(f"[helius] stream error @{url}: {exc!s}")
                    await asyncio.sleep(2)
            # rotate preference after a failure round-robin
            try_order.reverse()

    # -------------------------------------------------------------------- #
    # Helper used by scripts/run_live.py ---------------------------------- #
    def launch_helius_stream(loop: asyncio.AbstractEventLoop) -> None:
        loop.create_task(helius_stream_task())

    # -------------------------------------------------------------------- #
    # awaited by core.synergy_conductor.conductor
    async def get_next_tick(timeout: float | None = None) -> dict | None:
        """
        Async read of the inbound Helius queue.
        Returns None on timeout so the caller can keep its own loop cadence.
        """
        try:
            return await asyncio.wait_for(helius_queue.get(), timeout)
        except asyncio.TimeoutError:
            return None
