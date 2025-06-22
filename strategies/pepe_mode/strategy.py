from __future__ import annotations
import time, pathlib, yaml
from agents import TradeSignal
from core.risk_manager.manager import RiskManager

PARAMS = yaml.safe_load((pathlib.Path("config") / "pepe_params.yaml").read_text())


class Strategy:
    """Narrative momentum tail strategy."""

    def __init__(self):
        self.risk_mgr = RiskManager.instance()

    async def decide(self, mkt_tick) -> TradeSignal | None:
        # if self.risk_mgr.capital_tier() < 5:
        #     raise ValueError(5)

        score = mkt_tick.get("momentum_score", 0.0)
        tier = self.risk_mgr.capital_tier()
        theta = PARAMS["theta"][tier]

        if score >= theta:
            size = self.risk_mgr.position_limit_usd() * 0.06
            return TradeSignal(
                action="BUY_HOLD_PEP",
                token=mkt_tick["token"],
                size_usd=size,
                aux={"score": score},
                confidence=min(1.0, score),
            )
        return None
