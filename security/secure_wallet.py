"""
secure_wallet.py
Phase 10.1 – Loads wallet from secrets.json or .env
Signs transactions using solana-py or raw base58 decode.
"""
# when it loads secrets.json:
# "secret_key": [144,99,30,135,132,205,131,74,183,242,53,150,21,255,156,130,132,195,205,138,72,144,224,8,106,224,236,229,130,79,66,163,92,85,56,116,68,170,83,53,180,84,160,202,182,49,134,206,219,217,144,62,199,81,142,151,51,154,226,129,210,174,81,103],

# Then we can sign and send from that Keypair

import os
import json
from pathlib import Path
from typing import Optional

from solana.publickey import PublicKey
from solana.keypair import Keypair
from solana.rpc.async_api import AsyncClient
from solana.transaction import Transaction

# We'll store a single global wallet instance for convenience
_G_KEYPAIR: Optional[Keypair] = None

def load_keypair() -> Keypair:
    global _G_KEYPAIR
    if _G_KEYPAIR is not None:
        return _G_KEYPAIR

    # read secrets.json
    secret_path = Path("config/secrets.json")
    if not secret_path.exists():
        raise FileNotFoundError("No config/secrets.json for wallet!")
    data = json.loads(secret_path.read_text())
    if "secret_key" not in data:
        raise ValueError("secrets.json missing 'secret_key' field")

    # "secret_key" is either array of 64 ints or base58?
    raw = data["secret_key"]
    if isinstance(raw, str):
        # base58 decode
        from solana.keypair import Keypair
        from solana.rpc import types
        from base58 import b58decode
        raw_bytes = b58decode(raw)
        _G_KEYPAIR = Keypair.from_secret_key(raw_bytes)
    elif isinstance(raw, list):
        # assume list[int]
        _G_KEYPAIR = Keypair.from_secret_key(bytes(raw))
    else:
        raise ValueError("secret_key format not recognized")

    return _G_KEYPAIR

async def sign_and_send(
    tx: Transaction, rpc_url: str, commitment: str = "confirmed"
) -> str:
    """Sign with our global Keypair, send via raw solana-py client."""
    kp = load_keypair()
    async with AsyncClient(rpc_url, commitment=commitment) as client:
        tx.sign(kp)
        resp = await client.send_transaction(tx, kp)
        # optionally confirm
        # await client.confirm_transaction(resp.value)
        sig = resp.value
        return sig
