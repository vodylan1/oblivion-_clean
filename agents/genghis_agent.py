from agents.base import Agent, AgentMeta, TradeSignal
from drafts.market_data import MarketData


class GenghisAgent(Agent):
    meta = AgentMeta(
        name="GenghisAgent",
        version="0.1",
        risk_profile="conquest",
        description="All‑in conquest agent on whale inflow",
    )

    async def logic(self, market_data: MarketData):
        if market_data.whale_inflow >= 1_000 and market_data.meme_hype >= 60:
            return TradeSignal(action="BUY", confidence=1.0, meta={"agent": self.meta.name})
        if market_data.whale_inflow < 100 and market_data.volatility > 35:
            return TradeSignal(action="SELL", confidence=1.0, meta={"agent": self.meta.name})
        return TradeSignal(action="HOLD", confidence=0.4, meta={"agent": self.meta.name})
