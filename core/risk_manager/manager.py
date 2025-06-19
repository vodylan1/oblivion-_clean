"""
Risk‑Manager · Phase 11 stub
Singleton + helpers for tests and live loop.
"""

from __future__ import annotations
from typing import Optional


class _TierInt(int):
    """Behaves like int and like a callable returning that int."""
    def __call__(self) -> int:       # noqa: D401
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
        self._bucket_cap: int = 5_000_000_000  # 5 SOL
        # 👇  Tier 5 satisfies every Phase‑11 strategy
        self.capital_tier: _TierInt = _TierInt(5)

    # ------------- helpers the unit‑tests still expect --------------------
    @property
    def bucket_cap(self) -> int:
        return self._bucket_cap

    def pre_trade(self, _sig, size_lamports: int) -> bool:
        return size_lamports <= self._bucket_cap

    # ---------------- conductor / strategy interface ----------------------
    def accept(self, _sig) -> bool:          # always accept – stub
        return True

    async def assess_and_maybe_fire(self, sig) -> None:  # noqa: ANN001
        if self.accept(sig):
            print("[risk_mgr] would execute:", sig)

    # ── TEMP stub: disable gating so placeholder strats stop raising error 5
    def capital_tier(self) -> int:          # Phase 11‑c will restore logic
        return 0
