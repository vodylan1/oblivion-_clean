"""
RiskManager v2  – now capital‑aware
"""

from __future__ import annotations
from typing import Dict, List

from core.capital_manager.capital_class import CapitalTier, classify_equity


class RiskManager:
    """Tracks PnL & enforces cVaR + bankroll tier limits."""

    def __init__(self) -> None:
        self._equity_history: List[float] = []     # USD snapshots
        self.current_tier: CapitalTier = CapitalTier.MICRO

    # ──────────────────────────────────────────────
    # public

    def register_equity(self, equity_usd: float) -> None:
        self._equity_history.append(equity_usd)
        self.current_tier = classify_equity(equity_usd)

    def position_limit_usd(self) -> float:
        # naive cVaR clamp: 1 % of equity capped by tier table
        equity = self._equity_history[-1] if self._equity_history else 0
        max_pct = 0.01
        raw_cap = equity * max_pct
        from core.capital_manager.adaptive_strategy import apply_tier_overrides
        limits = apply_tier_overrides({}, self.current_tier)
        return min(raw_cap, limits["max_trade_usd"])

    # placeholder – real VaR calc in Phase 12
    def value_at_risk(self) -> float:
        return 0.0
