"""
Risk-Manager · Phase 11 stub
Singleton + helpers for tests and live loop.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

# --- delegate to the PR-queue RiskManager pipeline --------------------------
try:
    # local pipeline stub in tests / full impl in prod
    from pipelines.risk_manager import position_limit_usd as _pl_limit
except ModuleNotFoundError:  # fallback → current in-core impl
    _pl_limit = None

from config.parameters import VAR_CAP_RATIO, BUY_LOW_CONF
from pipelines.secure_wallet import get_wallet_balance_usd
from pipelines.position_manager import get_open_positions_usd


# ────────────────────────────────────────────────────────────────────────────
def position_limit_usd() -> Decimal:
    """
    Return how much USD we may safely deploy on the *next* buy.
    Delegates to pipelines.risk_manager when present.
    """
    if _pl_limit is not None:          # new delegate
        return _pl_limit()
    # ── legacy logic (kept for safety) ──────────────────────────────────────
    balance  = get_wallet_balance_usd()
    cap      = balance * Decimal(VAR_CAP_RATIO)
    if BUY_LOW_CONF:
        cap /= 2
    open_pos = get_open_positions_usd()
    return max(Decimal("0"), cap - open_pos)


# ────────────────────────────────────────────────────────────────────────────
class _TierInt(int):
    """Behaves like int and like a callable returning that int."""

    def __call__(self) -> int:  # noqa: D401
        return int(self)


class RiskManager:
    _INSTANCE: Optional["RiskManager"] = None

    # -------------------------------------------------------------- singleton
    def __new__(cls, *a, **kw):
        if cls._INSTANCE is not None:
            raise RuntimeError("RiskManager is a singleton; use .instance()")
        inst = super().__new__(cls)
        cls._INSTANCE = inst
        return inst

    @classmethod
    def instance(cls) -> "RiskManager":
        if cls._INSTANCE is None:
            cls._INSTANCE = cls()
        return cls._INSTANCE

    # ------------------------------------------------------------------ init
    def __init__(self) -> None:
        self._bucket_cap: int = 5_000_000_000  # 5 SOL
