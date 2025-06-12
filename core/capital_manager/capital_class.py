"""
capital_class.py
--------------------------------------------------------
Maps USD equity → discrete tier label for downstream logic.
"""

from __future__ import annotations
from enum import Enum, auto


class CapitalTier(Enum):
    MICRO = auto()   # 0‑5 k USD
    SMALL = auto()   # 5‑25 k
    MID   = auto()   # 25‑100 k
    LARGE = auto()   # 100‑500 k
    WHALE = auto()   # 500 k+

    @property
    def idx(self) -> int:        # for array indexing
        return list(CapitalTier).index(self)


_THRESHOLDS = {  # lower‑bound USD
    CapitalTier.MICRO: 0,
    CapitalTier.SMALL: 5_000,
    CapitalTier.MID:   25_000,
    CapitalTier.LARGE: 100_000,
    CapitalTier.WHALE: 500_000,
}


def classify_equity(equity_usd: float) -> CapitalTier:
    tier = CapitalTier.MICRO
    for t, bound in _THRESHOLDS.items():
        if equity_usd >= bound:
            tier = t
    return tier
