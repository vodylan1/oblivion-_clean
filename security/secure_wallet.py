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

import os, base64, json, asyncio, aiohttp
from typing import List

from solders.keypair import Keypair
from solders.transaction import Transaction

from .key_store import load_keypair          # your existing helper

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

JITO_RELAY = os.getenv(        # override for other regions if desired
    "JITO_RELAY",
    "https://mainnet.block-engine.jito.wtf/api/v1/bundles",
).rstrip("/")

JITO_AUTH = os.getenv("JITO_AUTH")            # optional – leave unset for 1 RPS


# ---------------------------------------------------------------------------
# Core API – sign & submit
# ---------------------------------------------------------------------------

async def sign_and_send(txs: List[Transaction], wallet_name: str) -> str:
    """
    Sign each tx with the fee‑payer keypair, submit as bundle, return base‑58
    signature of the first transaction.
    """
    kp: Keypair = load_keypair(wallet_name)

    # sign + b64 encode
    bundle = {
        "transactions": [
            base64.b64encode(bytes(tx.sign([kp]))).decode() for tx in txs
        ]
    }

    headers: dict[str, str] = {}
    if JITO_AUTH:
        headers["Authorization"] = f"Bearer {JITO_AUTH}"

    async with aiohttp.ClientSession() as sess:
        async with sess.post(JITO_RELAY, json=bundle, headers=headers, timeout=5) as r:
            body = await r.text()
            if r.status != 200:
                raise RuntimeError(f"Jito error {r.status}: {body}")

            return json.loads(body)["signature"]


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
