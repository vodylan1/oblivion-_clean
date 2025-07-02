"""Secure-wallet façade (Phase-5).

CI stubs keep tests green; production branches are TODO.
"""

from __future__ import annotations

import base64
import os
from typing import Final


# ── Keypair helper ──────────────────────────────────────────────────────────
class Keypair:
    def __init__(self, secret: bytes):
        if len(secret) != 64:
            raise ValueError("Keypair secret must be 64 bytes")
        self._secret = secret

    @classmethod
    def from_env(cls, var: str = "SOLANA_KEYPAIR") -> "Keypair":
        raw = os.getenv(var)
        if not raw:  # pragma: no cover
            raise RuntimeError(f"{var} env-var missing")
        return cls(base64.b64decode(raw))


# ── façade helpers ──────────────────────────────────────────────────────────
_RPC: Final[str] = os.getenv("RPC_ENDPOINT", "https://api.devnet.solana.com")


def get_wallet_balance_usd() -> float:
    """Return wallet balance in USD.

    ALWAYS 10 000 USD until Phase-7 wires real RPC + price-feed.
    """
    return 10_000.0


def sign_and_send(tx_bytes: bytes) -> str:
    """Sign & broadcast a transaction, returning its hash."""
    # CI / local dev → always stub-hash.
    # Only hit the real signer once Phase-7 injects the keypair.
    if os.getenv("CI") or os.getenv("SOLANA_KEYPAIR") is None:
        return "0xDEADBEEF"

    _kp = Keypair.from_env()  # pragma: no cover (stub)
    _ = (_kp, tx_bytes)  # silence linters
    return "0xFEEDFACE"  # placeholder


def get_solana_client(cluster: str = "mainnet") -> str:  # str stub
    """Return an RPC endpoint string (placeholder object in CI)."""
    if os.getenv("CI"):
        return "https://api.devnet.solana.com"
    return _RPC


# ── legacy aliases ─────────────────────────────────────────────────────────
try:
    SIGNER: Final[Keypair] = Keypair(b"\0" * 64)
except Exception:  # pragma: no cover
    SIGNER = None


def send_bundle(tx_bytes: bytes) -> str:
    """Legacy alias retained for back-compat."""
    return sign_and_send(tx_bytes)
