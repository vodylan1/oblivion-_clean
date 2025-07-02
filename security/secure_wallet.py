'''Stubbed secure-wallet helpers for CI.

In production this would communicate with a signer or key‑vault; for the test
suite we just provide deterministic stand‑ins so imports and basic functionality
resolve without network access or private keys.
'''
from __future__ import annotations

from dataclasses import dataclass
from typing import Final

# ── constants & fakes ─────────────────────────────────────────────────────
_FAKE_SIG: Final[str] = "0xDEADBEEF"

# ── public helpers used in pipelines / strategies ─────────────────────────

def get_wallet_balance_usd() -> float:  # noqa: D401
    """Hard‑coded USD balance so risk tests have something deterministic."""
    return 10_000.0


def sign_and_send(tx_bytes: bytes) -> str:  # noqa: D401
    """Pretend we signed & broadcasted the transaction; return a fake hash."""
    return _FAKE_SIG


def send_bundle(*_a, **_k) -> str:  # noqa: D401
    """Fake ‘bundle‑send’; always returns the same signature string."""
    return _FAKE_SIG


# ── minimal Solana Keypair placeholder (needed by jito_submit & ping) ─────

@dataclass(slots=True)
class Keypair:
    """Dummy Solana keypair stand‑in for CI."""

    pubkey: str = "So11111111111111111111111111111111111111112"
    secret: bytes | None = None


# Alias required by ping.strategy
SIGNER: Keypair = Keypair()

# (any real production helpers or position_limit_usd policy stubs may follow)
