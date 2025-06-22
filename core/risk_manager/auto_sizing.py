"""
auto_sizing.py
────────────────────────────────────────────────────────────────────────────
Phase 10 – references CVaR=8.8% from alpha-stable tail fitting
scales synergy or agent pos sizing if daily drawdown triggers.

We store daily PnL in a ring or do time-based check.
"""

import time


class AutoSizeManager:
    def __init__(self):
        self.cvar_daily_95 = 0.088  # from the 4-o stable tail fit
        self.daily_loss_cut = 0.09  # we use 9% as the threshold
        self.scale_factor = 1.0

        self._today_str = self._date_str()
        self._start_equity = 0.0

    def _date_str(self) -> str:
        return time.strftime("%Y-%m-%d")

    def on_new_day(self, equity_now: float):
        # reset
        self._today_str = self._date_str()
        self._start_equity = equity_now
        self.scale_factor = 1.0

    def on_equity_update(self, equity_now: float) -> None:
        """
        Called every synergy cycle with current total eq or PnL.
        If daily dd>9%, scale down size by 30%.
        """
        if self._date_str() != self._date_str():
            # day changed
            self.on_new_day(equity_now)
            return

        if self._start_equity <= 0:
            return

        dd = (self._start_equity - equity_now) / self._start_equity
        if dd >= self.daily_loss_cut:
            self.scale_factor = 0.7  # reduce size to 70%


auto_sizer = AutoSizeManager()
