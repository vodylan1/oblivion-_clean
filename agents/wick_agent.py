from agents.base import Agent, AgentMeta, TradeSignal
from drafts.market_data import MarketData


class WickAgent(Agent):
    meta = AgentMeta(
        name="WickAgent",
        version="0.1",
        risk_profile="aggressive",
        description="High‑velocity sniper agent",
    )

    def __init__(self):
        self._prev_price = None

    async def logic(self, market_data: MarketData):
        if market_data.meme_hype > 75 and market_data.volatility > 20:
            return TradeSignal(action="BUY", confidence=0.9, meta={"agent": self.meta.name})
        if (
            self._prev_price
            and market_data.meme_hype < 40
            and market_data.price < self._prev_price * 0.97
        ):
            return TradeSignal(action="SELL", confidence=0.9, meta={"agent": self.meta.name})
        self._prev_price = market_data.price
        return TradeSignal(action="HOLD", confidence=0.5, meta={"agent": self.meta.name})
