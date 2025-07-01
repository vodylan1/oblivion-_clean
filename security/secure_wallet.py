from __future__ import annotations

"""
Minimal, test-only wallet helper.

Phase-4 will replace this with the real secure-signing façade.
"""

from typing import Final

# Hard-coded dummy balance so CI has something deterministic
_FAKE_BALANCE_USD: Final[float] = 10_000.0


def get_wallet_balance_usd() -> float:  # noqa: D401
    """Return wallet USD value (stub)."""
    return _FAKE_BALANCE_USD
