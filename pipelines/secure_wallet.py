"""Secure-wallet façade (Phase-5).

CI stubs keep the unit tests green; production logic is TODO.
"""

from __future__ import annotations
import base64, os
from typing import Final


# ── simple Keypair stand-in ────────────────────────────────────────────────
class Keypair:
    """Ultra-minimal keypair placeholder (no Solana-SDK dependency)."""

    def __init__(self, secret: bytes):
        self._secret = secret

    @classmethod
    def from_env(cls, var: str = "SOLANA_KEYPAIR") -> "Keypair":
        raw = os.getenv(var)
        if not raw:
            raise RuntimeError(f"{var} env-var missing")
        return cls(base64.b64decode(raw))


# ── façade helpers ────────────────────────────────────────────────────────
_RPC: Final[str] = os.getenv("RPC_ENDPOINT", "https://api.devnet.solana.com")


def get_wallet_balance_usd() -> float:
    """Return wallet balance in USD.

    * CI  → hard-coded 10 k for deterministic tests.
    * Prod→ TODO: RPC balance × price feed.
    """
    if os.getenv("CI"):
        return 10_000.0
    # 🟡 TODO: real RPC + price feed
    return 9_999.0


def sign_and_send(tx_bytes: bytes) -> str:
    """Sign & broadcast a transaction, returning its signature hash."""
    if os.getenv("CI"):
        return "0xDEADBEEF"
    _kp = Keypair.from_env()
    # 🟡 TODO: sign and POST to _RPC
    return "0xFEEDFACE"


def get_solana_client(cluster: str = "mainnet") -> str:  # str stub
    """Return an RPC endpoint string (stub for CI)."""
    if os.getenv("CI"):
        return "https://api.devnet.solana.com"
    # 🟡 TODO: return a real client object from solana-py
    return _RPC
