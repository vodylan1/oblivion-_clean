"""Stubbed secure-wallet helpers for CI.

In production this module will talk to a signer/key-vault and a real Solana RPC
endpoint.  For the test-suite we supply deterministic stand-ins so imports
resolve without network access or private keys.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

# ─────────────────────────────────────────────────────────────────────────────
# Constants & fakes
# ─────────────────────────────────────────────────────────────────────────────
SIGNER_PUBKEY: Final[str] = "So11111111111111111111111111111111111111112"
_FAKE_SIG: Final[str] = "0xDEADBEEF"


# ─────────────────────────────────────────────────────────────────────────────
# Public helpers expected by pipelines / strategies
# ─────────────────────────────────────────────────────────────────────────────
def get_wallet_balance_usd() -> float:  # noqa: D401
    """Return a hard-coded wallet balance so risk tests stay deterministic."""
    return 10_000.0


def sign_and_send(tx_bytes: bytes) -> str:
    """Pretend we signed & broadcasted the transaction; always return fake sig."""
    # `tx_bytes` is ignored in the stub; real implementation signs & sends.
    return _FAKE_SIG


def send_bundle(*_txs: bytes) -> str:
    """Batch-send helper required by some strategies (e.g., ping / jito paths)."""
    return _FAKE_SIG


# ─────────────────────────────────────────────────────────────────────────────
# Minimal Solana Keypair stub – satisfies `pipelines.jito_submit` imports
# ─────────────────────────────────────────────────────────────────────────────
@dataclass(slots=True)
class Keypair:
    """Dummy Solana keypair stand-in for CI and docs.

    Only exposes the attributes accessed by the codebase: `.pubkey` and
    optionally `.secret`. Nothing else is required for the test suite.
    """

    pubkey: str = SIGNER_PUBKEY
    secret: bytes | None = None


# Alias used by various modules to reference the hot signer key.
SIGNER: Keypair = Keypair()


# ─────────────────────────────────────────────────────────────────────────────
# Optional stub RPC client – satisfies `rug_checker` tests without network
# ─────────────────────────────────────────────────────────────────────────────
def get_solana_client(_cluster: str | None = None):  # accepts devnet/mainnet arg
    """Return a fake RPC client object so imports succeed in offline CI."""

    class _FakeClient:
        def get_balance(self, *_a, **_kw):
            # Mirror Solana RPC balance response shape
            return {"result": {"value": 0}}

    return _FakeClient()
