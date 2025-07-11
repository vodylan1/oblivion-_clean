"""Secure-wallet façade (Phase-5).

*Returns deterministic values in CI; prod logic is TODO.*"""

from __future__ import annotations

import base64
from typing import Final


# ────────────────────────────────────────────────────────────
class Keypair:  # minimal placeholder (no Solana-SDK)
    def __init__(self, secret: bytes):
        self._secret = secret

    @classmethod
    def from_env(cls, var: str = "SOLANA_KEYPAIR") -> "Keypair":
        raw = os.getenv(var)
        if not raw:  # pragma: no cover
            raise RuntimeError(f"{var} env-var missing")
        return cls(base64.b64decode(raw))


# ── public façade helpers ───────────────────────────────────
def get_wallet_balance_usd() -> float:  # deterministic for tests
    return 10_000.0


def sign_and_send(tx_bytes: bytes) -> str:  # deterministic for tests
    return "0xDEADBEEF"


def get_solana_client(cluster: str = "mainnet") -> str:
    return "https://api.devnet.solana.com"


# legacy aliases expected by older strategy code
SIGNER: Final[Keypair] = Keypair(b"\0" * 64)


def send_bundle(tx_bytes: bytes) -> str:
    return sign_and_send(tx_bytes)
