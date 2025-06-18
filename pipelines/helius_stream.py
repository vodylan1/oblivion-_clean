"""
pipelines/helius_stream.py
──────────────────────────
• Connects to the Helius WebSocket with your API key.
• Subscribes to all stealth wallets + Raydium/Orca pools.
• Exposes an asyncio.Queue so the SynergyConductor can pull fresh ticks.
"""

from __future__ import annotations
import os, json, aiohttp, asyncio
from pathlib import Path
from typing import Dict, Any, List

HELIUS_KEY = os.getenv("HELIUS_API_KEY")
WS_URL     = f"wss://stream.helius.xyz/v0/solana/mainnet?api-key={HELIUS_KEY}"
POOL_FILE  = Path("wallets/stealth_pool.json")

QUEUE: asyncio.Queue[Dict[str, Any]] = asyncio.Queue(maxsize=1_000)

# ---------------------------------------------------------------------------

async def _build_subscribe_payload() -> str:
    wallets: List[str] = [
        w["pubkey"]
        for w in json.loads(POOL_FILE.read_text())["wallets"]
    ]

    # example liquidity‑pool pubkeys (replace / extend as needed)
    wallets += [
        "Epa6mHpGnjZai3ibxYpokW9XiWFL7SmktDCN8hTLB1Uy",  # Raydium WSOL/USDC pool
        "7s5k7e3Tz6m6xko4fLeDR7GkfjNq8Mw2F1dRG9a7fU9y",  # Orca   WSOL/USDC pool
    ]

    return json.dumps({
        "jsonrpc": "2.0",
        "id":      1,
        "method":  "accountSubscribe",
        "params":  [wallets, {"encoding": "base64", "commitment": "processed"}]
    })

# ---------------------------------------------------------------------------

async def helius_stream_task() -> None:
    if not HELIUS_KEY:
        print("[helius] API key missing – stream disabled")
        return

    async with aiohttp.ClientSession() as sess, \
               sess.ws_connect(WS_URL, autoping=True, heartbeat=15) as ws:

        await ws.send_str(await _build_subscribe_payload())
        print("[helius] subscribed")

        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                await QUEUE.put_nowait(json.loads(msg.data))
            elif msg.type == aiohttp.WSMsgType.ERROR:
                print("[helius] WS error", msg)
                break

# ---------------------------------------------------------------------------

async def get_next_tick() -> Dict[str, Any]:
    """Conductor awaits this for the next live update."""
    return await QUEUE.get()
