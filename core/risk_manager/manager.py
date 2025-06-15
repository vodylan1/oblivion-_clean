"""
Risk‑Manager (Phase 9 stub upgraded for Phase 11)
─────────────────────────────────────────────────
* Singleton accessor via RiskManager.instance()
* Bucket‑cap sizing helper for legacy tests
* capital_tier() callable used by Phase 11 strategies
  (returns 1 so strategies do not abort on tier 0)
"""

from __future__ import annotations
from typing import Optional, Any


class RiskManager:
    _INSTANCE: Optional["RiskManager"] = None

    # ------------------------------------------------------------------
    def __new__(cls, *args, **kwargs):  # noqa: D401
        if cls._INSTANCE is not None:
            raise RuntimeError("RiskManager is a singleton; use RiskManager.instance()")
        inst = super().__new__(cls)
        cls._INSTANCE = inst
        return inst

    # ------------------------------------------------------------------
    @classmethod
    def instance(cls) -> "RiskManager":
        if cls._INSTANCE is None:
            cls._INSTANCE = cls()
        return cls._INSTANCE

    # ------------------------------------------------------------------
    # constructors / config
    def __init__(self) -> None:
        # basic bucket sizing stub (5 SOL)
        self._bucket_cap: int = 5_000_000_000

    # ------------------------------------------------------------------
    # =====  SIMPLE HELPERS REQUIRED BY TESTS & STRATEGIES  ============

    @property
    def bucket_cap(self) -> int:
        """Maximum lamports a single trade may use (legacy tests)."""
        return self._bucket_cap

    def pre_trade(self, signal: "TradeSignal", size_lamports: int) -> bool:  # noqa: F821
        """Return True if the trade is within the current bucket cap."""
        return size_lamports <= self._bucket_cap

    # Phase 11 strategy helper
    def capital_tier(self) -> int:
        """
        Return risk‑tier integer.
        Tier 0 would disable several strategies; we start at Tier 1.
        """
        return 1

    # ------------------------------------------------------------------
    # =====  MAIN RISK CHECK USED BY CONDUCTOR  ========================

    def accept(self, signal: "TradeSignal") -> bool:  # noqa: F821
        """
        Basic always‑accept placeholder.
        Real VaR / exposure logic lands in Phase 12.
        """
        return True

    async def assess_and_maybe_fire(self, signal: "TradeSignal") -> None:  # noqa: F821
        """
        Placeholder async hook invoked by conductor in live mode.
        """
        if self.accept(signal):
            # Real TX dispatch goes here in Phase 12
            print("[risk_mgr] would execute:", signal)
        else:
            print("[risk_mgr] rejected:", signal)
