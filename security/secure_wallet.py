"""
secure_wallet.py
Phase 10.1 – load keypair from secrets.json and sign transactions.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from base58 import b58decode
from solana.keypair import Keypair
from solana.rpc.async_api import AsyncClient
from solana.transaction import Transaction

# single global cache
_KP: Optional[Keypair] = None


def load_keypair() -> Keypair:
    global _KP
    if _KP is not None:
        return _KP

    secret_path = Path("config/secrets.json")
    if not secret_path.exists():
        raise FileNotFoundError("config/secrets.json missing")

    data = json.loads(secret_path.read_text())
    raw = data["secret_key"]
    if isinstance(raw, str):
        _KP = Keypair.from_secret_key(b58decode(raw))
    elif isinstance(raw, list):
        _KP = Keypair.from_secret_key(bytes(raw))
    else:
        raise ValueError("secret_key format not recognised")
    return _KP


async def sign_and_send(tx: Transaction, rpc_url: str) -> str:
    kp = load_keypair()
    async with AsyncClient(rpc_url) as cli:
        tx.sign(kp)
        sig = (await cli.send_transaction(tx, kp)).value
        return sig


# ---------------------------------------------------------------- legacy shim
def get_solana_client(rpc_url: str | None = None):
    """
    Legacy helper for rug_checker test – returns **sync** Client.
    """
    from solana.rpc.api import Client  # local import
    return Client(rpc_url or "https://api.mainnet-beta.solana.com")
