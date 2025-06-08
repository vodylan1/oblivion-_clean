from agents.base import Agent, AgentMeta, TradeSignal
from drafts.market_data import MarketData


class TywinAgent(Agent):
    meta = AgentMeta(
        name="TywinAgent",
        version="0.1",
        risk_profile="defensive",
        description="Conservative capital‑preservation agent",
    )

    async def logic(self, market_data: MarketData):
        if market_data.meme_hype > 90 or market_data.volatility > 40:
            return TradeSignal(action="SELL", confidence=0.8, meta={"agent": self.meta.name})
        if market_data.price < market_data.lp_depth / 10_000:
            return TradeSignal(action="BUY_LOW_CONF", confidence=0.8, meta={"agent": self.meta.name})
        return TradeSignal(action="HOLD", confidence=0.5, meta={"agent": self.meta.name})
