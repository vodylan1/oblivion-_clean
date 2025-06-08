from agents.base import Agent, AgentMeta, TradeSignal
from drafts.market_data import MarketData


class JohanAgent(Agent):
    meta = AgentMeta(
        name="JohanAgent",
        version="0.1",
        risk_profile="paranoia",
        description="Meta‑agent that blocks risky consensus",
    )

    async def logic(self, market_data: MarketData):
        if market_data.volatility > 45 or market_data.meme_hype > 90:
            return TradeSignal(action="HOLD", confidence=0.95, meta={"agent": self.meta.name})
        # For now default HOLD; in Phase 8 will read Conductor state
        return TradeSignal(action="HOLD", confidence=0.5, meta={"agent": self.meta.name})
