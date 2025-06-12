"""
Capital‑Manager package
Phase 10.2  ·  Classifies current bankroll into tiers and exposes
helpers so every strategy can query trade‑sizing limits.
"""

from .capital_class import CapitalTier, classify_equity  # noqa: F401
from .adaptive_strategy import apply_tier_overrides       # noqa: F401

__all__: list[str] = [
    "CapitalTier",
    "classify_equity",
    "apply_tier_overrides",
]
