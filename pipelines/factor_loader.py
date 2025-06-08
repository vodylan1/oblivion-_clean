# pipelines/factor_loader.py
"""
Transforms raw on‑chain + social feeds into the 32‑dim
feature vector expected by ScoringEngine.  Each helper
function is pure so it can be unit‑tested in isolation.
"""

from __future__ import annotations

from math import log10
from typing import Dict, List

import numpy as np
import pandas as pd


# helper ──────────────────────────────────────
def _safe_pct(a: float, b: float) -> float:
    return 0.0 if b == 0 else 100.0 * (a / b - 1)


def encode_features(token_snapshot: Dict[str, float | int]) -> List[float]:
    """
    Convert a *merged* snapshot (price, lp, whale, social, safety…) into the
    32‑element model vector, ordered exactly as docs/factor_spec.md.
    Unknown or N/A fields are filled with 0.
    """
    f = token_snapshot  # alias
    out: list[float] = []

    # 1‑4 price action
    out.append(_safe_pct(f.get("price_now", 0), f.get("price_1h", 1)))
    out.append(_safe_pct(f.get("price_now", 0), f.get("price_24h", 1)))
    out.append(_safe_pct(f.get("price_now", 0), f.get("price_7d", 1)))
    out.append(
        0
        if f.get("max_30d", 0) == f.get("min_30d", 0)
        else (f["price_now"] - f["min_30d"]) / (f["max_30d"] - f["min_30d"])
    )

    # 5 24h perf rank placeholder (computed later by batch normaliser)
    out.append(f.get("perf_rank_24h", 0))

    # 6‑9 volatility
    out += [
        f.get("vol_24h", 0),
        f.get("vol_7d", 0),
        f.get("intraday_range", 0),
        f.get("vol_rank", 0),
    ]

    # 10‑14 liquidity / usage
    out += [
        log10(f.get("liq_now", 1) + 1),
        _safe_pct(f.get("liq_now", 0), f.get("liq_24h", 1)),
        log10(f.get("vol_usd_24h", 1) + 1),
        f.get("vol_usd_24h", 0) / max(f.get("liq_now", 1), 1),
        log10(f.get("unique_traders_24h", 1) + 1),
    ]

    # 15‑18 whale
    out += [
        f.get("whale_net_inflow", 0),
        f.get("whale_concentration", 0),
        f.get("whale_count", 0),
        f.get("whale_buy_sell_ratio", 0),
    ]

    # 19‑25 social
    out += [
        log10(f.get("tweets_per_h", 1) + 1),
        f.get("tw_sentiment", 0),
        log10(f.get("tg_msgs_per_h", 1) + 1),
        f.get("tg_sentiment", 0),
        f.get("gtrend_idx", 0),
        f.get("social_rank", 0),
        _safe_pct(f.get("social_today", 0), f.get("social_yday", 1)),
    ]

    # 26‑32 safety
    out += [
        f.get("renounced", 0),
        f.get("verified", 0),
        f.get("lp_lock_days", 0),
        f.get("dev_share", 0),
        f.get("dev_outflow_24h", 0),
        f.get("tax_change_flag", 0),
        f.get("tax_rate", 0),
    ]

    assert len(out) == 32, f"Feature length mismatch ({len(out)})"
    return out
