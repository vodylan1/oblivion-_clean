"""Secure‑wallet façade.

•  CI **or** missing key‑pair → deterministic stubs keep unit‑tests hermetic.
•  PROD (Phase‑8) will wire in Solana‑py / Helius / HSM.
"""

from __future__ import annotations

import base64
import os
from typing import Final


# ───────── ultra‑light key‑pair placeholder ─────────
class Keypair:
    def __init__(self, secret: bytes):
        self._secret = secret

    @classmethod
    def from_env(cls, var: str = "SOLANA_KEYPAIR") -> "Keypair":
        blob = os.getenv(var)
        if not blob:  # pragma: no cover
            raise RuntimeError(f"{var} env‑var missing")
        return cls(base64.b64decode(blob))


# ───────── high‑level façade helpers ─────────
_RPC: Final[str] = os.getenv("RPC_ENDPOINT", "https://api.devnet.solana.com")
_STUB_SIG: Final[str] = "0xDEADBEEF"


def get_wallet_balance_usd() -> float:
    """Return wallet balance in USD (deterministic stub until Phase‑8)."""
    return 10_000.0  # keep constant for every unit‑test


def sign_and_send(tx_bytes: bytes) -> str:
    """Return a tx‑signature hash.

    • CI **or** missing key‑pair → stub sig
    • Prod → TODO: sign & POST to _RPC (Phase‑8)
    """
    if os.getenv("CI") or not os.getenv("SOLANA_KEYPAIR"):
        return _STUB_SIG

    _kp = Keypair.from_env()
    # 🟡 TODO: real signing & send
    return "0xFEEDFACE"


def get_solana_client(cluster: str = "mainnet") -> str:  # simple str stub
    return "https://api.devnet.solana.com" if os.getenv("CI") else _RPC


# ───── back‑compat shims required by legacy code ─────
SIGNER: Final[Keypair] = Keypair(b"\0" * 64)  # dummy signer


def send_bundle(tx_bytes: bytes) -> str:
    """Alias kept for strategies.ping.strategy etc."""
    return sign_and_send(tx_bytes)
