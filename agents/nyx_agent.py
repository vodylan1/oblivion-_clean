from agents.base import Agent, AgentMeta, TradeSignal
from core.common.market_data import MarketData
from pipelines.mev_stealth import jitter


class NyxAgent(Agent):
    meta = AgentMeta(
        name="NyxAgent",
        version="0.1",
        risk_profile="stealth",
        description="MEV‑aware sniper with tx timing jitter",
    )

    async def logic(self, market_data: MarketData):
        if market_data.meme_hype > 65 and 20 < market_data.volatility < 40:
            # introduce non‑blocking jitter
            await jitter(200)
            return TradeSignal(action="BUY", confidence=0.9, meta={"agent": self.meta.name})
        return TradeSignal(action="HOLD", confidence=0.5, meta={"agent": self.meta.name})
