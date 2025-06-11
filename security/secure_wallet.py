"""
secure_wallet.py
Phase 10.1 – load hot wallet from secrets or env & sign + send.
Compatible with both solana-py 0.29 (solders) and older versions.
"""

from __future__ import annotations

import json, os
from pathlib import Path
from typing import Optional

# ------------------------------------------------------------------ Keypair import
try:
    # solana-py ≤ 0.36
    from solana.keypair import Keypair  # type: ignore
except ImportError:  # solana-py 0.29+
    from solders.keypair import Keypair  # type: ignore

from solana.rpc.async_api import AsyncClient
from solana.transaction import Transaction
from base58 import b58decode

# -------------------------------------------------------------------- globals
_KP: Optional[Keypair] = None


# -------------------------------------------------------------------- helpers
def _load_secret_key() -> Keypair:
    """
    Resolve Keypair from:
      1. env WALLET_SECRET_BASE58   (single base58 string)
      2. config/secrets.json { "base58": "...", or "secret_key": [int] }
    """
    if (b58 := os.getenv("WALLET_SECRET_BASE58")):
        return Keypair.from_secret_key(b58decode(b58))

    cfg = Path("config/secrets.json")
    if not cfg.exists():
        raise FileNotFoundError("config/secrets.json not found and WALLET_SECRET_BASE58 not set")

    data = json.loads(cfg.read_text())
    if "base58" in data:
        return Keypair.from_secret_key(b58decode(data["base58"]))
    if isinstance(data.get("secret_key"), list):
        return Keypair.from_secret_key(bytes(data["secret_key"]))

    raise ValueError("No usable secret_key in secrets.json")


# -------------------------------------------------------------------- public API
def wallet() -> Keypair:
    global _KP
    if _KP is None:
        _KP = _load_secret_key()
    return _KP


async def sign_and_send(tx: Transaction, rpc_url: str) -> str:
    """Sign with hot wallet and send.  Returns signature string."""
    kp = wallet()
    async with AsyncClient(rpc_url, commitment="confirmed") as cli:
        tx.sign(kp)
        resp = await cli.send_transaction(tx, kp)
        return resp.value
