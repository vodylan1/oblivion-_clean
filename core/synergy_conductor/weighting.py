"""Rolling-Sharpe weight updater (canonical)."""

from __future__ import annotations
import statistics

def update_weights(pnl_dict: dict[str, list[float]]) -> dict[str, float]:
    """Map 50-trade Sharpe → weight 0-2, with small-sample decay."""
    weights: dict[str, float] = {}
    for agent, pnl in pnl_dict.items():
        window = pnl[-50:]
        n = len(window)
        if n < 2:
            sharpe = 0.0
        else:
            mean = statistics.mean(window)
            stdev = statistics.pstdev(window) or 1e-9
            sharpe = mean / stdev
        raw = max(0.0, min(2.0, 1.0 + sharpe / 2))
        if n < 20:
            alpha = n / 20.0
            raw = 1.0 * (1 - alpha) + raw * alpha
        weights[agent] = raw
    return weights
