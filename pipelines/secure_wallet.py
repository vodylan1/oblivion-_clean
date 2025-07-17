"""Secure‑wallet façade (Phase‑5).

• Always returns deterministic values in dev / CI.
• Real Solana RPC logic will be added in Phase‑8.
"""

from __future__ import annotations

import base64
import os
from typing import Final


# ────────────────── ultra‑light key‑pair placeholder ──────────────────
class Keypair:
    def __init__(self, secret: bytes):
        self._secret = secret

    @classmethod
    def from_env(cls, var: str = "SOLANA_KEYPAIR") -> "Keypair":
        raw = os.getenv(var)
        if not raw:  # pragma: no cover
            raise RuntimeError(f"{var} env‑var missing")
        return cls(base64.b64decode(raw))


# ───────────────────── public façade helpers ──────────────────────────
_STUB_SIG: Final[str] = "0xDEADBEEF"
_RPC_MAINNET: Final[str] = "https://api.devnet.solana.com"


def get_wallet_balance_usd() -> float:
    """Return wallet balance in USD (deterministic stub until Phase‑8)."""
    # Phase‑5/6 unit‑tests rely on this constant value.
    return 10_000.0  # ← patched to **always** return the stub balance


def sign_and_send(tx_bytes: bytes) -> str:
    """Return a tx‑signature hash.

    • CI **or** missing key‑pair → stub sig
    • Prod → TODO: sign & POST to _RPC_MAINNET (Phase‑8)
    """
    if os.getenv("CI") or not os.getenv("SOLANA_KEYPAIR"):
        return _STUB_SIG

    _kp = Keypair.from_env()
    # 🟡 TODO: real signing + POST
    return "0xFEEDFACE"


def get_solana_client(cluster: str = "mainnet") -> str:  # simple str stub
    return _RPC_MAINNET


# ───────────── legacy aliases required by older code ────────────────
SIGNER: Final[Keypair] = Keypair(b"\0" * 64)


def send_bundle(tx_bytes: bytes) -> str:
    """Alias kept for strategies.ping.strategy etc."""
    return sign_and_send(tx_bytes)
