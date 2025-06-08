# core/risk_manager/manager.py
"""
RiskManager v1.0
• Rolling 96‑h VaR per token
• Portfolio max draw‑down guard
• USD bucket caps
"""

from __future__ import annotations

import os
from collections import deque
from typing import Deque, Dict

from agents import TradeSignal


def _env_float(key: str, default: float) -> float:
    try:
        return float(os.getenv(key, default))
    except ValueError:
        return default


class RiskManager:
    _INSTANCE: "RiskManager | None" = None

    @classmethod
    def instance(cls) -> "RiskManager":
        if cls._INSTANCE is None:
            cls._INSTANCE = cls()
        return cls._INSTANCE

    # ────────────────────────────────────────────
    def __init__(self) -> None:
        self.var_window_h = int(_env_float("VAR_LOOKBACK_H", 96))
        self.max_dd_pct = _env_float("MAX_DD_PCT", 15.0)
        self.bucket_cap = _env_float("OBLIVION_BUCKET_SIZE_USD", 250)

        self._price_hist: Dict[str, Deque[float]] = {}
        self._equity_hist: Deque[float] = deque(maxlen=self.var_window_h * 60)

    # ────────────────────────────────────────────
    def mark_equity(self, equity_usd: float) -> None:
        self._equity_hist.append(equity_usd)

    def register_price(self, token: str, price: float) -> None:
        dq = self._price_hist.setdefault(token, deque(maxlen=self.var_window_h * 60))
        dq.append(price)

    # ────────────────────────────────────────────
    def pre_trade(self, sig: TradeSignal, exposure_after_usd: float) -> bool:
        if exposure_after_usd > self.bucket_cap:
            return False

        if len(self._equity_hist) > 1:
            peak = max(self._equity_hist)
            trough = min(self._equity_hist)
            dd_pct = 100.0 * (peak - trough) / (peak or 1)
            if dd_pct > self.max_dd_pct:
                return False

        hist = self._price_hist.get(sig.meta.get("token", ""), None)
        if hist and len(hist) >= 120:
            returns = [(hist[i] - hist[i - 1]) / hist[i - 1] for i in range(1, len(hist))]
            returns.sort()
            var_95 = abs(returns[int(0.05 * len(returns))]) * 100
            if abs(sig.meta.get("pct_move", 0)) > var_95:
                return False

        return True
