"""
Auto‑Tuner
~~~~~~~~~~
Monitors portfolio VaR and draw‑down; adjusts open‑order size and
priority‑fee bias in real time.

* EVT tail fitted (Generalised Pareto, 95 % threshold) on 96 h window
* Pydantic config for live hot‑reload
* Emits `TuningSignal` consumed by `Sentinel`
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Optional

import numpy as np
from pydantic import BaseModel, Field, PositiveFloat

# ————————————————————————————————————————————
class AutoTuneCfg(BaseModel):
    var_lookback_h: PositiveFloat = Field(
        default=float(os.getenv("VAR_LOOKBACK_H", "96")),
        description="History window (hours) for VaR & EVT tail‑fit.",
    )
    max_dd_pct: PositiveFloat = Field(
        default=float(os.getenv("MAX_DD_PCT", "15")),
        description="Max accepted draw‑down (absolute, %).",
    )


class TuningSignal(BaseModel):
    """Down‑stream order‑sizing hint."""
    size_multiplier: float
    prio_fee_multiplier: float
    comment: str


# ————————————————————————————————————————————
_EVT_CACHE = Path(".tmp/evt_tail.json")


def _fit_evt_tail(returns: np.ndarray, thresh: float = 0.95) -> tuple[float, float]:
    """
    Fit Generalised‑Pareto tail (shape ξ, scale β) above empirical quantile `thresh`.
    Very small, single‑pass estimation (Pickands).
    """
    if returns.size < 50:  # not enough data
        return 0.0, 1.0
    u = np.quantile(returns, thresh)
    excess = returns[returns > u] - u
    if excess.size < 10:
        return 0.0, 1.0
    log_excess = np.log(excess)
    xi = 0.5 * (np.mean(log_excess) - np.log(np.mean(excess)))  # Pickands
    beta = (1 + xi) * np.mean(excess)
    # cache (debug / offline checks)
    _EVT_CACHE.parent.mkdir(exist_ok=True)
    _EVT_CACHE.write_text(json.dumps({"xi": xi, "beta": beta, "u": float(u)}))
    return float(xi), float(beta)


# ————————————————————————————————————————————
class AutoTuner:
    """Singleton auto‑tuner with rolling buffer."""
    _INSTANCE: Optional["AutoTuner"] = None

    @classmethod
    def instance(cls) -> "AutoTuner":
        if cls._INSTANCE is None:
            cls._INSTANCE = cls()
        return cls._INSTANCE

    # ———
    def __init__(self) -> None:
        self.cfg = AutoTuneCfg()
        self._pnl_history: list[float] = []

    # ———
    def update_pnl(self, pnl: float) -> None:
        """Append new PnL data‑point (in percent)."""
        self._pnl_history.append(pnl)
        # trim to last N hours (assume 1 point / h for stub)
        max_len = int(self.cfg.var_lookback_h)
        if len(self._pnl_history) > max_len:
            self._pnl_history = self._pnl_history[-max_len :]

    # ———
    def tune(self) -> TuningSignal:
        """Return live size / fee multipliers given risk constraints."""
        if len(self._pnl_history) < 10:
            return TuningSignal(size_multiplier=1.0, prio_fee_multiplier=1.0, comment="Bootstrapping")

        ret = np.array(self._pnl_history) / 100.0  # pct → fraction
        # 1‑day 99 % VaR
        var_99 = np.quantile(ret, 0.01) * 100

        # EVT tail for extreme risk
        xi, beta = _fit_evt_tail(ret)

        # draw‑down
        cum = np.cumsum(ret)
        peak = np.maximum.accumulate(cum)
        dd = np.min(cum - peak) * 100  # %

        # multipliers
        size_mult = 1.0
        fee_mult = 1.0
        if abs(dd) > self.cfg.max_dd_pct:
            size_mult *= 0.5
            fee_mult *= 0.5
        if var_99 < -self.cfg.max_dd_pct * 0.7:
            size_mult *= 0.7
        if xi > 0.3:  # fat tail detected
            fee_mult *= 1.3

        comment = f"VaR99={var_99:.2f}% dd={dd:.2f}% xi={xi:.3f}"
        return TuningSignal(size_multiplier=size_mult, prio_fee_multiplier=fee_mult, comment=comment)
