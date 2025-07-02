"""
pipelines.risk_manager
Delegates position-sizing for the next buy.

⚠️  Keep this *free* of imports from core.risk_manager.manager to avoid cycles.
"""

from decimal import Decimal
from typing import Final

# ── config knobs pulled in once at import time ────────────────────────────
try:
    from config.parameters import VAR_CAP_RATIO, BUY_LOW_CONF  # noqa: F401
except ModuleNotFoundError:  # tests / CI
    VAR_CAP_RATIO: Final[float] = 0.25
    BUY_LOW_CONF: Final[bool] = False

# cheap, side-effect-free helpers
from pipelines.position_manager import get_open_positions_usd
from security.secure_wallet import get_wallet_balance_usd  # ← path fixed


def position_limit_usd() -> Decimal:
    """
    Max fresh USD we may allocate on the *next* buy.
    Pure function – no network / disk side-effects.
    """
    balance = get_wallet_balance_usd()
    cap = balance * Decimal(VAR_CAP_RATIO)
    if BUY_LOW_CONF:
        cap /= 2
    open_pos = Decimal(get_open_positions_usd())
    return max(Decimal("0"), cap - open_pos)
