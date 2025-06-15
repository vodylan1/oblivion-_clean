from __future__ import annotations
from agents import TradeSignal
from core.risk_manager.manager import RiskManager
import yaml, pathlib

PARAMS = yaml.safe_load((pathlib.Path("config") / "whale_params.yaml").read_text())

class Strategy:
    def __init__(self):
        self.risk_mgr = RiskManager.instance()

    async def decide(self, mkt_tick):
        flow = mkt_tick.get("whale_flow_usd", 0.)
        zscore = mkt_tick.get("price_z", 0.)
        tier = self.risk_mgr.capital_tier()

        if flow >= PARAMS["min_flow"][tier] and zscore >= PARAMS["min_z"]:
            size = min(flow * 0.25, self.risk_mgr.position_limit_usd()*0.08)
            return TradeSignal(
                action="FOLLOW_WHALE",
                token=mkt_tick["token"],
                size_usd=size,
                aux={"flow": flow, "z": zscore},
                confidence=0.8,
            )
        return None
