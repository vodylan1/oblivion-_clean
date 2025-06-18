"""
security/secure_wallet.py
─────────────────────────
Phase‑11 bundle signer for Oblivion.

• Signs one or more `solders.transaction.Transaction` objects with the chosen
  stealth wallet key‑pair.
• Submits them as an atomic bundle to Jito Block‑Engine via JSON‑RPC POST.
• Works with the public endpoint (no token) or with a JWT/UUID token when
  `JITO_AUTH` is set.

Dependencies: aiohttp, solders              (both already in requirements)
"""

from __future__ import annotations

import os, base64, json, asyncio, aiohttp
from typing import List

from solders.keypair import Keypair
from solders.transaction import Transaction

# ---------- configuration -----------------------------------------------------

# Regional endpoints: mainnet / frankfurt / tokyo / amsterdam
JITO_RELAY = os.getenv(
    "JITO_RELAY",
    "https://mainnet.block-engine.jito.wtf/api/v1/bundles",
).rstrip("/")  # safety

JITO_AUTH = os.getenv("JITO_AUTH")  # optional

# Import your existing helper that loads keypairs from disk / Ledger
from .key_store import load_keypair    # type: ignore

# ---------- core API ----------------------------------------------------------

async def sign_and_send(txs: List[Transaction], wallet_name: str) -> str:
    """
    • `txs` : list of *unsigned* Transaction objects (fee‑payer already set).
    • `wallet_name` : label that `load_keypair(name)` understands.

    Returns the first transaction's signature (base‑58) on success.
    Raises RuntimeError on non‑200 response.
    """
    kp: Keypair = load_keypair(wallet_name)

    # Sign & base‑64 encode each tx
    b64_txs: list[str] = []
    for tx in txs:
        signed = tx.sign([kp])
        b64_txs.append(base64.b64encode(bytes(signed)).decode())

    bundle_body = {"transactions": b64_txs}

    headers: dict[str, str] = {}
    if JITO_AUTH:                       # optional token for higher RPS
        headers["Authorization"] = f"Bearer {JITO_AUTH}"

    async with aiohttp.ClientSession() as sess:
        async with sess.post(
            JITO_RELAY,
            json=bundle_body,
            headers=headers,
            timeout=5,
        ) as resp:
            text = await resp.text()
            if resp.status != 200:
                raise RuntimeError(f"Jito error {resp.status}: {text}")

            return json.loads(text)["signature"]  # base‑58 str


# Convenience wrapper for callers that send only one tx
async def send_single(tx: Transaction, wallet_name: str) -> str:
    return await sign_and_send([tx], wallet_name)


# ---------- minimal throttle helper (optional) --------------------------------
# If you want to guarantee ≤1 bundle/sec on the public tier,
# wrap your call in `await throttle()`.
_last_bundle_ts: float = 0.0

async def throttle(min_gap_sec: float = 1.05) -> None:
    global _last_bundle_ts
    now = asyncio.get_event_loop().time()
    sleep_for = (_last_bundle_ts + min_gap_sec) - now
    if sleep_for > 0:
        await asyncio.sleep(sleep_for)
    _last_bundle_ts = asyncio.get_event_loop().time()
