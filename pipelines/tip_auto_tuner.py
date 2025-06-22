"""
tip_auto_tuner.py
────────────────────────────────────────────────────────────────────────────
Phase 10 – rolling 20-slot congestion measure → lamports_per_cu

We store a small ring buffer of accept vs dropped tx to get ~ percentile.
"""

import collections
import math
import random


class TipAutoTuner:
    def __init__(self):
        self.window_size = 20
        self.data = collections.deque(maxlen=self.window_size)
        self.mapping = [
            (0.50, 500),
            (0.80, 900),
            (0.90, 1300),
            (0.97, 2000),
            (1.00, 3500),
        ]

    def record_slot(self, accept_count: int, drop_count: int):
        if accept_count + drop_count == 0:
            ratio = 0.0
        else:
            ratio = drop_count / (accept_count + drop_count)
        self.data.append(ratio)

    def get_tip_lamports(self) -> int:
        if not self.data:
            return 500  # default
        ratio_avg = sum(self.data) / len(self.data)  # average drop ratio
        # interpret ratio as approximate percentile
        # naive approach: ratio ~ congestion percentile
        cum = 0.0
        for thresh, tip in self.mapping:
            if ratio_avg <= thresh:
                return tip
        return self.mapping[-1][1]


# global instance
tip_auto_tuner = TipAutoTuner()
