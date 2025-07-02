"""Stubbed secure-wallet helpers for CI.

In production this talks to the signer / key-vault; for tests we just pretend.
"""
from __future__ import annotations
from typing import Final

# ── constants & fakes ─────────────────────────────────────────────────────
SIGNER: Final[str] = "stub-signer-pubkey"
_FAKE_SIG: Final[str] = "0xDEADBEEF"

# ── public helpers used in pipelines / strategies ─────────────────────────
def get_wallet_balance_usd() -> float:  # noqa: D401
    """Hard-coded balance so risk tests have something deterministic."""
    return 10_000.0


def sign_and_send(tx_bytes: bytes) -> str:
    """Pretend we signed & broadcasted the tx; return a fake hash."""
    return _FAKE_SIG


def send_bundle(*_txs: bytes) -> str:
    """Batch-send helper expected by various strategies (e.g., ping.strategy)."""
    return _FAKE_SIG

# (any other helpers—such as a position_limit_usd policy—should remain below)
