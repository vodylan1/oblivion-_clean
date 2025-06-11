"""
secure_wallet.py
────────────────────────────────────────────────────────────
• Loads keypair from config/secrets.json   (base58 OR int‑array)
• Handles both old *solana-py* < 0.29   and   new ≥ 0.29 / solders.
• Exposes `sign_and_send()`   and a sync  `get_solana_client()` shim
  required by legacy rug‑checker tests.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Union, Sequence

from base58 import b58decode

# ----------------------------------------------------------------─ keypair import
try:  # solana‑py <= 0.28 -------------
    from solana.keypair import Keypair  # type: ignore
except ModuleNotFoundError:  # solana‑py ≥ 0.29  (Keypair moved to solders)
    from solders.keypair import Keypair  # type: ignore
    from solders.pubkey import Pubkey as PublicKey  # noqa: F401  (back‑compat)
else:  # <=0.28 still has PublicKey in same pkg
    from solana.publickey import PublicKey  # noqa: F401  (kept for linter)

from solana.rpc.async_api import AsyncClient
from solana.rpc.api import Client           # sync shim
from solana.transaction import Transaction

_KP: Optional[Keypair] = None        # singleton cache

# ----------------------------------------------------------------─ helpers
def _load_raw_secret() -> Union[str, Sequence[int]]:
    secret_path = Path("config/secrets.json")
    if not secret_path.exists():
        raise FileNotFoundError("‼️  config/secrets.json missing")
    data = json.loads(secret_path.read_text())
    if "secret_key" not in data:
        raise KeyError("'secret_key' not in secrets.json")
    return data["secret_key"]


def load_keypair() -> Keypair:
    """Return cached Keypair, creating it the first time."""
    global _KP
    if _KP is not None:
        return _KP

    raw = _load_raw_secret()
    if isinstance(raw, str):
        _KP = Keypair.from_secret_key(b58decode(raw))
    elif isinstance(raw, (list, tuple)):
        _KP = Keypair.from_secret_key(bytes(raw))
    else:
        raise ValueError("secret_key must be base58 str OR list[int]")
    return _KP


async def sign_and_send(tx: Transaction, rpc_url: str) -> str:
    """
    Sign with our wallet and post to *rpc_url*.
    Returns the signature string.
    """
    kp = load_keypair()
    async with AsyncClient(rpc_url) as cli:
        tx.sign(kp)
        sig = (await cli.send_transaction(tx, kp)).value
        return sig


# ----------------------------------------------------------------─ legacy shim
def get_solana_client(rpc_url: str | None = None) -> Client:  # noqa: D401
    """
    Legacy sync client used by rug_checker tests.
    """
    return Client(rpc_url or "https://api.mainnet-beta.solana.com")
