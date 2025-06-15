"""
Risk‑Manager (Phase 11 stub)
────────────────────────────
Singleton with helpers needed by tests and Trump‑Card strategies.
"""

from __future__ import annotations
from typing import Optional, Any


# ── helper: callable integer wrapper ─────────────────────────────────
class _TierInt(int):                               # noqa: D401
    """`tier = risk_mgr.capital_tier` gives int; tier() also returns int."""

    # pylint: disable=no-self-use
    def __call__(self) -> int:                     # type: ignore[override]
        return int(self)


# ── Risk‑Manager singleton ───────────────────────────────────────────
class RiskManager:
    _INSTANCE: Optional["RiskManager"] = None

    # ------------------------------------------------------------------
    def __new__(cls, *args, **kwargs):  # noqa: D401
        if cls._INSTANCE is not None:
            raise RuntimeError("RiskManager is a singleton; use RiskManager.instance()")
        inst = super().__new__(cls)
        cls._INSTANCE = inst
        return inst

    @classmethod
    def instance(cls) -> "RiskManager":
        if cls._INSTANCE is None:
            cls._INSTANCE = cls()
        return cls._INSTANCE

    # ------------------------------------------------------------------
    def __init__(self) -> None:
        self._bucket_cap: int = 5_000_000_000   # 5 SOL cap

        # Provide BOTH attribute and callable semantics
        self.capital_tier: _TierInt = _TierInt(3)    # Tier 3 starter

    # ===== Tests helpers =================================================
    @property
    def bucket_cap(self) -> int:
        return self._bucket_cap

    def pre_trade(self, _signal: "TradeSignal", size_lamports: int) -> bool:  # noqa: F821
        return size_lamports <= self._bucket_cap

    # ===== Main accept logic (stub) ======================================
    def accept(self, _signal: "TradeSignal") -> bool:  # noqa: F821
        return True

    async def assess_and_maybe_fire(self, signal: "TradeSignal") -> None:  # noqa: F821
        if self.accept(signal):
            print("[risk_mgr] would execute:", signal)
        else:
            print("[risk_mgr] rejected:", signal)
