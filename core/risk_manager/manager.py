"""
Central risk-sizing façade (“RiskManager”).

Phase-3 goal: expose a single `.pre_trade()` gate and
a live-refresh bucket-cap sourced from `risk_policies.*`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from config.parameters import VAR_CAP_RATIO
from risk_policies import load_policy
from security.secure_wallet import get_wallet_balance_usd
from trade_types import (  # ← restored path
    TradeSide,
    TradeSignal,
    TradeResult,
)

# ──────────────────────────────────────────────────────────────
# helpers
# ──────────────────────────────────────────────────────────────


@dataclass(slots=True)
class _RuntimeCaps:
    """Holds live-computed USD limits."""

    bucket_cap: float = 0.0

    def refresh(self) -> None:
        bal = get_wallet_balance_usd()
        policy = load_policy()  # defaults to static_25
        self.bucket_cap = policy.position_limit_usd(bal)


# ──────────────────────────────────────────────────────────────
# singleton
# ──────────────────────────────────────────────────────────────


class RiskManager:
    """Singleton orchestrating all pre-trade risk checks."""

    _INSTANCE: "RiskManager | None" = None

    # global VAR guard (not wired yet)
    _var_cap_ratio: Final[float] = VAR_CAP_RATIO

    def __init__(self) -> None:
        self._caps = _RuntimeCaps()
        self._caps.refresh()

    # ---------- factory ---------- #

    @classmethod
    def instance(cls) -> "RiskManager":
        if cls._INSTANCE is None:
            cls._INSTANCE = cls()
        return cls._INSTANCE

    # ---------- live data ---------- #

    @property
    def bucket_cap(self) -> float:  # noqa: D401
        """USD limit per token bucket."""
        return self._caps.bucket_cap

    # ---------- public check ---------- #

    def pre_trade(self, signal: TradeSignal, notional_usd: float) -> bool:
        """
        Return **True** if the proposed trade passes risk rules.

        Currently enforced:
        • bucket-cap
        • (stub) global VAR cap
        """
        if notional_usd > self.bucket_cap:
            return False
        # TODO: VAR enforcement once equity curve is wired
        return True
