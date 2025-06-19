"""
Jito bundle submitter + local key‑load helper.
Success / fail counts are recorded by pipelines.jito_metrics.
"""

from __future__ import annotations
import os, aiohttp, base64, json, pathlib

JITO_RELAY = os.getenv("JITO_RELAY", "https://mainnet.block-engine.jito.wtf/api/v1/bundles")

# ------------------------------------------------------------------ #
# 🔑 Minimal key‑loader stub – replace with real keystore in phase 12
def load_keypair(name: str) -> tuple[bytes, str]:
    """
    Returns (private_key_bytes, pubkey_base58) for the first stealth wallet.
    Reads from wallets/stealth_pool.json at repo root.
    """
    pool = pathlib.Path(__file__).resolve().parents[1] / "wallets/stealth_pool.json"
    data = json.loads(pool.read_text())
    pk  = data["wallets"][0]["pubkey"]
    return b"\0" * 64, pk              # zero‑privkey placeholder

# ------------------------------------------------------------------ #
from pipelines.jito_metrics import record_ok, record_fail


async def sign_and_send(raw_tx_b64: str) -> None:
    """
    Wraps a base64‑encoded raw transaction into a Jito bundle and POSTs it.
    Counts metrics on every response.
    """
    _priv, pubkey = load_keypair("stealth-0")

    bundle = {
        "transactions": [raw_tx_b64],
        "simulatedTransactions": [],
        "leader": None,
        "rejectionReason": "",           # ignored by relay
        "referenceBlock": 0,
    }

    headers = {"Content-Type": "application/json"}

    async with aiohttp.ClientSession() as sess:
        resp = await sess.post(JITO_RELAY, json=bundle, headers=headers, timeout=3)
        if resp.status == 200:
            record_ok()
        else:
            try:
                js = await resp.json()
                record_fail(js.get("message", str(resp.status)))
            except Exception:
                record_fail(str(resp.status))
        resp.raise_for_status()          # raise after counting
