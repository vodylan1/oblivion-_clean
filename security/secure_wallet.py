"""
Secure‑wallet helper (unit‑test stub).
Compatible with solana‑py 0.29.x  (Keypair lives in `solders` wheels).
"""
from __future__ import annotations
import json, pathlib, os
from typing import Any

try:                                # solana‑py ≤0.30
    from solana.keypair import Keypair
except ModuleNotFoundError:         # fallback for 0.29 build
    from solders.keypair import Keypair

_KEY_PATH = pathlib.Path("oblivion_key.json")


# ---------------------------------------------------------------------
def _load_raw_secret() -> list[int]:
    if not _KEY_PATH.exists():
        # create  by default for unit tests (unsafe for prod!)
        kp = Keypair()
        _KEY_PATH.write_text(json.dumps(list(kp.to_bytes())))
        return list(kp.to_bytes())
    return json.loads(_KEY_PATH.read_text())


def load_keypair() -> Keypair:
    return Keypair.from_bytes(bytes(_load_raw_secret()))


# ---------------------------------------------------------------------
async def sign_and_send(tx: Any, rpc_url: str) -> str:  # noqa: ANN401
    """
    Dummy implementation – just returns a fake signature in tests.
    Real signer will send through Jito bundle relay in live mode.
    """
    print(f"[secure_wallet] sign_and_send → {rpc_url}")
    return os.urandom(32).hex()

# ---------------------------------------------------------------------
def get_solana_client(rpc_url: str = "https://api.mainnet-beta.solana.com") -> object:
    """
    Dummy RPC client for unit tests.
    Real implementation will return `AsyncClient` from solana‑py.
    """
    class _Client:                   # noqa: D401
        def __init__(self, url: str) -> None:
            self.endpoint = url
        async def get_balance(self, pubkey: str) -> dict:     # type: ignore[override]
            return {"result": {"value": 10_000_000_000}}      # 10 SOL stub
    return _Client(rpc_url)
