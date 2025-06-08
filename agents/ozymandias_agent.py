from agents.base import Agent, AgentMeta, TradeSignal
from drafts.market_data import MarketData


class OzymandiasAgent(Agent):
    meta = AgentMeta(
        name="OzymandiasAgent",
        version="0.1",
        risk_profile="builder",
        description="Empire‑builder DCA agent",
    )

    def __init__(self):
        self._last_price = None

    async def logic(self, market_data: MarketData):
        action = "HOLD"
        conf = 0.5
        if (
            market_data.meme_hype >= 55
            and market_data.lp_depth >= 50_000
            and self._last_price
            and market_data.price < self._last_price * 0.995
        ):
            action = "BUY"
            conf = 0.85
        self._last_price = market_data.price
        return TradeSignal(action=action, confidence=conf, meta={"agent": self.meta.name})
