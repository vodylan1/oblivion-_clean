from __future__ import annotations
from decimal import Decimal


class Policy:
    """Static 25 % VaR cap; halves if balance < $500."""

    VAR_CAP = Decimal("0.25")
    LOW_BAL_THRESHOLD = Decimal("500")

    def allowance(self, balance: Decimal, open_pos: Decimal) -> Decimal:
        cap = balance * self.VAR_CAP
        if balance < self.LOW_BAL_THRESHOLD:
            cap /= 2
        return cap - open_pos
