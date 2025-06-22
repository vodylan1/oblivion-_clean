"""
adaptive_strategy.py
--------------------------------------------------------
Given a CapitalTier, returns dicts of parameter overrides
for sniper, arb, MM, etc.  (Phase 10.2 – minimal heuristic)
"""

from __future__ import annotations
from typing import Dict, Any

from .capital_class import CapitalTier

# ── static ruleset table ────────────────────────────────────────────────────
# Feel free to edit these numbers by config env later.
_TABLE: Dict[CapitalTier, Dict[str, Any]] = {
    CapitalTier.MICRO: {
        "max_trade_usd": 300,
        "min_pool_depth_usd": 10_000,
        "slip_bps": 300,  # 3 %
    },
    CapitalTier.SMALL: {
        "max_trade_usd": 1_000,
        "min_pool_depth_usd": 50_000,
        "slip_bps": 200,
    },
    CapitalTier.MID: {
        "max_trade_usd": 4_000,
        "min_pool_depth_usd": 150_000,
        "slip_bps": 150,
    },
    CapitalTier.LARGE: {
        "max_trade_usd": 15_000,
        "min_pool_depth_usd": 400_000,
        "slip_bps": 100,
    },
    CapitalTier.WHALE: {
        "max_trade_usd": 50_000,
        "min_pool_depth_usd": 1_000_000,
        "slip_bps": 60,
    },
}


def apply_tier_overrides(params: Dict[str, Any], tier: CapitalTier) -> Dict[str, Any]:
    """
    Shallow‑copy *params*, overlay tier overrides, return new dict.
    """
    merged = dict(params)
    merged.update(_TABLE[tier])
    return merged
