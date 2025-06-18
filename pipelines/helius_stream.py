# --- replace the existing helius_stream.py entirely -------------------

from __future__ import annotations
import os, json, aiohttp, asyncio
from pathlib import Path
from typing import Dict, Any, List

HELIUS_KEY = os.getenv("HELIUS_API_KEY")
WS_URL     = f"wss://stream.helius.xyz/v0/solana/mainnet?api-key={HELIUS_KEY}"
POOL_FILE  = Path("wallets/stealth_pool.json")
QUEUE: asyncio.Queue[Dict[str, Any]] = asyncio.Queue(maxsize=1_000)


def _stealth_pubkeys() -> List[str]:
    data = json.loads(POOL_FILE.read_text())
    return [w["pubkey"] for w in data["wallets"]]


# ---------------------------------------------------------------------------

async def helius_stream_task() -> None:
    if not HELIUS_KEY:
        print("[helius] API key missing – stream disabled")
        return

    try:
        async with aiohttp.ClientSession() as sess, \
                   sess.ws_connect(WS_URL, autoping=True, heartbeat=15) as ws:

            # subscribe each account individually
            for pk in _stealth_pubkeys():
                await ws.send_json({
                    "jsonrpc": "2.0",
                    "id":      pk,
                    "method":  "accountSubscribe",
                    "params":  [pk, {"encoding": "base64", "commitment": "processed"}],
                })
            print("[helius] subscribed to", len(_stealth_pubkeys()), "accounts")

            async for msg in ws:
                if msg.type is aiohttp.WSMsgType.TEXT:
                    await QUEUE.put_nowait(json.loads(msg.data))

    except Exception as exc:
        print("[helius] stream error:", exc)


async def get_next_tick() -> Dict[str, Any]:
    return await QUEUE.get()
