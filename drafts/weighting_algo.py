"""
Rolling‑Sharpe weight updater
Range‑clamped to 0‑2 and decays toward 1.0 if <20 trades.
"""

from __future__ import annotations

import statistics
from typing import Dict, List


def _sharpe(pnls: List[float]) -> float:
    if len(pnls) < 2:  # not enough data for stdev
        return 0.0
    mean = statistics.mean(pnls)
    std = statistics.pstdev(pnls)
    if std == 0:
        return float("inf") if mean > 0 else -float("inf") if mean < 0 else 0.0
    return mean / std


def update_weights(pnls: Dict[str, List[float]]) -> Dict[str, float]:
    out: Dict[str, float] = {}
    for agent, all_trades in pnls.items():
        window = all_trades[-50:]  # last 50
        n = len(window)
        sharpe = _sharpe(window)
        raw = 1.0 + sharpe / 2.0  # map −2→0, 0→1, +2→2
        raw = 0.0 if raw < 0 else 2.0 if raw > 2 else raw
        if n < 20:  # linear decay toward 1.0
            alpha = n / 20.0
            raw = 1.0 * (1 - alpha) + raw * alpha
        out[agent] = raw
    return out


# quick sanity test (run `python weighting_algo.py`)
if __name__ == "__main__":  # pragma: no cover
    weights = update_weights(
        {
            "good": [0.5] * 50,
            "bad": [-0.5] * 50,
            "volatile": [1, -1] * 25,
            "small": [0.2] * 10,
        }
    )
    print(weights)
