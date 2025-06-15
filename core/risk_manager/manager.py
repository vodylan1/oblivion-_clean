"""
RiskManager v2.1  – singleton + capital‑aware sizing
"""

from __future__ import annotations
from typing import Dict, List

from core.capital_manager.capital_class import CapitalTier, classify_equity


class RiskManager:
    """Tracks PnL, bankroll tier and size limits (singleton)."""

    _INST: "RiskManager | None" = None

    # ── singleton helper ──────────────────────────
    @classmethod
    def instance(cls) -> "RiskManager":
        if cls._INST is None:
            cls._INST = cls()
        return cls._INST
    # ------------------------------------------------------------------
    @property
    def bucket_cap(self) -> int:
        """
        Maximum lamports allowed for the next trade bucket.
        Phase‑9 tests use this to verify position sizing.
        """
        return getattr(self, "_bucket_cap", 5_000_000_000)   # 5 SOL stub

    # Phase‑11 strategies query this attribute; until dynamic PnL sizing
    # lands in Phase 12 we hard‑code Tier 0.
    @property
    def capital_tier(self) -> int:
        return 0        # 0 = micro‑cap starter tier


    # ------------------------------------------------------------------
    def pre_trade(self, signal: "TradeSignal", size_lamports: int) -> bool:  # noqa: F821
        """
        Light‑weight check used in unit tests:
        returns True if the requested size is below current bucket cap.
        """
        return size_lamports <= self.bucket_cap

    # ── ctor ──────────────────────────────────────
    def __init__(self) -> None:
        if RiskManager._INST is not None:
            # enforce singleton – users should call instance()
            raise RuntimeError("RiskManager is a singleton; use RiskManager.instance()")
        self._equity_history: List[float] = []
        self.current_tier: CapitalTier = CapitalTier.MICRO

    # ── public API ────────────────────────────────
    def register_equity(self, equity_usd: float) -> None:
        self._equity_history.append(equity_usd)
        self.current_tier = classify_equity(equity_usd)

    def position_limit_usd(self) -> float:
        """Return the hard cap for a single trade, USD."""
        equity = self._equity_history[-1] if self._equity_history else 0
        raw_cap = equity * 0.01  # 1 % default risk slice

        from core.capital_manager.adaptive_strategy import apply_tier_overrides
        limits = apply_tier_overrides({}, self.current_tier)
        return min(raw_cap, limits["max_trade_usd"])

    # placeholder – real VaR calc in Phase 12
    def value_at_risk(self) -> float:
        return 0.0
