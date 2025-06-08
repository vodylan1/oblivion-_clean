import pytest
from agents.tywin_agent import TywinAgent
from agents.wick_agent import WickAgent
from drafts.market_data import MarketData


@pytest.mark.asyncio
async def test_tywin_sell():
    agent = TywinAgent()
    md = MarketData(price=1, lp_depth=1_000, meme_hype=95, whale_inflow=0, volatility=10)
    sig = await agent.logic(md)
    assert sig.action == "SELL"


@pytest.mark.asyncio
async def test_wick_buy():
    agent = WickAgent()
    md = MarketData(price=1, lp_depth=1_000, meme_hype=80, whale_inflow=0, volatility=25)
    sig = await agent.logic(md)
    assert sig.action == "BUY"
