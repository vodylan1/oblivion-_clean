"""
secure_wallet.py
Phase 10.1 – load keypair from secrets.json or env, sign & send tx.
"""

from __future__ import annotations

import json, os
from pathlib import Path
from typing import Optional

from solana.keypair import Keypair
from solana.rpc.async_api import AsyncClient
from solana.transaction import Transaction
from base58 import b58decode

# -------------------------------------------------------------------- globals
_KP: Optional[Keypair] = None


# -------------------------------------------------------------------- helpers
def _load_secret_key() -> Keypair:
    """
    Resolve the Keypair once.  Accepts:
      • env WALLET_SECRET_BASE58   (single base58 string)
      • config/secrets.json {"secret_key":[int,int,…] | "base58":"…"}
    """
    secret_env = os.getenv("WALLET_SECRET_BASE58")
    if secret_env:
        return Keypair.from_secret_key(b58decode(secret_env))

    cfg = Path("config/secrets.json")
    if not cfg.exists():
        raise FileNotFoundError("config/secrets.json missing and WALLET_SECRET_BASE58 not set")
    data = json.loads(cfg.read_text())
    if isinstance(data.get("secret_key"), list):
        return Keypair.from_secret_key(bytes(data["secret_key"]))
    if "base58" in data:
        return Keypair.from_secret_key(b58decode(data["base58"]))
    raise ValueError("No usable secret_key in secrets.json")


# -------------------------------------------------------------------- public
def wallet() -> Keypair:
    global _KP
    if _KP is None:
        _KP = _load_secret_key()
    return _KP


async def sign_and_send(tx: Transaction, rpc_url: str) -> str:
    """
    Sign with our hot wallet and send.  Returns tx signature.
    """
    kp = wallet()
    async with AsyncClient(rpc_url, commitment="confirmed") as cli:
        tx.sign(kp)
        resp = await cli.send_transaction(tx, kp)
        return resp.value  # signature string
