"""
helius_stream.py – verbose connectivity diagnostics
"""

from __future__ import annotations
import os, json, aiohttp, asyncio, traceback
from pathlib import Path
from typing import Dict, Any, List

HELIUS_KEY = os.getenv("HELIUS_API_KEY")
# ----- try both URL variants; v1 is the canonical endpoint (2025‑06)
WS_URL_V1 = f"wss://stream.helius.xyz/v0/solana/mainnet?api-key={HELIUS_KEY}"
WS_URL_V0 = f"wss://helius.rpcpool.com/?api-key={HELIUS_KEY}"  # legacy
POOL_FILE = Path("wallets/stealth_pool.json")
QUEUE: asyncio.Queue[Dict[str, Any]] = asyncio.Queue(maxsize=1_000)


def _pubkeys() -> List[str]:
    return [w["pubkey"] for w in json.loads(POOL_FILE.read_text())["wallets"]]


async def _run_ws(url: str) -> None:
    async with aiohttp.ClientSession() as sess, sess.ws_connect(
        url, autoping=True, heartbeat=15
    ) as ws:
        for pk in _pubkeys():
            await ws.send_json(
                {
                    "jsonrpc": "2.0",
                    "id": pk,
                    "method": "accountSubscribe",
                    "params": [pk, {"encoding": "base64", "commitment": "processed"}],
                }
            )
        print("[helius] subscribed via", url)
        async for msg in ws:
            if msg.type is aiohttp.WSMsgType.TEXT:
                await QUEUE.put_nowait(json.loads(msg.data))


async def helius_stream_task() -> None:
    if not HELIUS_KEY:
        print("[helius] API key missing – stream disabled")
        return

    for url in (WS_URL_V1, WS_URL_V0):
        try:
            await _run_ws(url)
            return  # exits only if connection closed cleanly
        except Exception as exc:
            print(
                f"[helius] connection failed on {url}: {exc.__class__.__name__} – {exc}"
            )
            traceback.print_exc()

    # if we reach here both URLs failed
    print("[helius] FATAL – no WebSocket endpoint reachable")


async def get_next_tick() -> Dict[str, Any]:
    return await QUEUE.get()
