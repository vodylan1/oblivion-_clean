"""
Secure‑Wallet · Phase 11.1
Signs transactions and submits Jito bundles via raw HTTP.
"""

from __future__ import annotations
import os, base64, json, aiohttp, asyncio
from typing import List

from solders.keypair import Keypair
from solders.transaction import Transaction
from .key_store import load_keypair          # <- your existing helper

JITO_RELAY = os.getenv(
    "JITO_RELAY",
    "https://frankfurt.mainnet.block-engine.jito.wtf/api/v1/bundles",
)
JITO_AUTH  = os.getenv("JITO_AUTH")          # <-- set this in shell


async def sign_and_send(txs: List[Transaction], wallet_name: str) -> str:
    """
    Sign each Transaction with `wallet_name` keypair, submit bundle, return signature str.
    """
    if JITO_AUTH is None:
        raise RuntimeError("JITO_AUTH env var missing")

    kp: Keypair = load_keypair(wallet_name)

    # sign & encode
    b64_txs = []
    for tx in txs:
        signed = tx.sign([kp])
        b64_txs.append(base64.b64encode(bytes(signed)).decode())

    bundle = {"transactions": b64_txs}

    async with aiohttp.ClientSession() as sess:
        headers = {"Authorization": f"Bearer {JITO_AUTH}"}
        async with sess.post(JITO_RELAY, json=bundle, headers=headers, timeout=5) as r:
            body = await r.text()
            if r.status != 200:
                raise RuntimeError(f"Jito error {r.status}: {body}")

            # Jito returns {"signature": "<first-tx-sig>", ...}
            sig = json.loads(body)["signature"]
            return sig


# convenience helper for single‑tx callers
async def send_single(tx: Transaction, wallet_name: str) -> str:
    return await sign_and_send([tx], wallet_name)
