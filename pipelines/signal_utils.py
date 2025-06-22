"""
Shared helpers for latency‑aware spread maths and misc signal utilities.
"""

from __future__ import annotations


def latency_spread(ray_ask: float, orca_bid: float, tip_pct: float = 0.0015) -> float:
    """
    Return the effective gross spread after subtracting latency / tip cost.

    * `ray_ask`  – best ask on Raydium
    * `orca_bid` – best bid on Orca
    * `tip_pct`  – extra % edge required to cover bundle tip  (default 0.15 %)

    Example:
        >>> latency_spread(99.8, 100.3)   # ≈ 0.0035 (0.35 %)
    """
    raw = (orca_bid - ray_ask) / ray_ask
    edge = raw - tip_pct
    return max(0.0, edge)
