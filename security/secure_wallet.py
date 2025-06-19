"""
security/secure_wallet.py
─────────────────────────
Phase‑11 bundle signer for Oblivion.

• Signs one or more solders.transaction.Transaction objects.
• Submits an atomic bundle to Jito Block‑Engine via HTTP POST.
• Works with the public (token‑less) tier or with a Bearer token when
  JITO_AUTH is exported.

Dependencies: aiohttp, solders  (already in requirements)
"""

from __future__ import annotations

import os, base64, json, asyncio
from typing import List
from aiohttp import ClientSession

from solders.keypair import Keypair
from solders.transaction import Transaction

from .key_store import load_keypair
from pipelines.jito_metrics import record_ok, record_fail  # ✅ metrics hook

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

JITO_RELAY = os.getenv(
    "JITO_RELAY",
    "https://mainnet.block-engine.jito.wtf/api/v1/bundles",
).rstrip("/")

JITO_AUTH = os.getenv("JITO_AUTH")  # optional – leave unset for 1 RPS


# ---------------------------------------------------------------------------
# Core API – sign & submit
# ---------------------------------------------------------------------------

async def sign_and_send(txs: List[Transaction], wallet_name: str) -> str:
    """
    Sign each tx with the fee‑payer keypair, submit as bundle, return base‑58
    signature of the first transaction.
    """
    kp: Keypair = load_keypair(wallet_name)

    payload = {
        "transactions": [
            base64.b64encode(bytes(tx.sign([kp]))).decode() for tx in txs
        ]
    }

    headers: dict[str, str] = {}
    if JITO_AUTH:
        headers["Authorization"] = f"Bearer {JITO_AUTH}"

    async with ClientSession() as sess:
        resp = await sess.post(JITO_RELAY, json=payload, headers=headers, timeout=3)

        if resp.status == 200:
            record_ok()
        else:
            try:
                js = await resp.json()
                record_fail(js.get("message", str(resp.status)))
            except Exception:
                record_fail(str(resp.status))

        resp.raise_for_status()  # still bubble up on error
        return (await resp.json())["signature"]


# Convenience wrapper
async def send_single(tx: Transaction, wallet_name: str) -> str:
    return await sign_and_send([tx], wallet_name)


# ---------------------------------------------------------------------------
# Optional simple throttle (≤1 req/s on public tier)
# ---------------------------------------------------------------------------

_last_ts: float = 0.0
async def throttle(min_gap_sec: float = 1.05) -> None:
    global _last_ts
    now = asyncio.get_event_loop().time()
    wait = (_last_ts + min_gap_sec) - now
    if wait > 0:
        await asyncio.sleep(wait)
    _last_ts = asyncio.get_event_loop().time()
