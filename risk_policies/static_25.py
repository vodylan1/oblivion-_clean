"""Static policy: limit each new position to MAX_PCT of current wallet USD balance."""
from typing import Final

MAX_PCT: Final[float] = 0.25      # 25 %

def position_limit_usd(balance_usd: float) -> float:
    """Return the USD cap for the next trade, given wallet balance."""
    return balance_usd * MAX_PCT
