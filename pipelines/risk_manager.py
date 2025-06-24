from decimal import Decimal
from core.risk_manager.manager import RiskManager

def position_limit_usd() -> Decimal:
    return RiskManager.instance().position_limit_usd()
