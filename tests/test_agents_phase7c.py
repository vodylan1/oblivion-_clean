import pytest
from agents.ozymandias_agent import OzymandiasAgent
from agents.johan_agent import JohanAgent
from agents.genghis_agent import GenghisAgent
from drafts.market_data import MarketData


@pytest.mark.asyncio
async def test_ozymandias_buy():
    a = OzymandiasAgent()
    # first tick sets _last_price
    await a.logic(MarketData(price=1.0, lp_depth=60_000, meme_hype=60, whale_inflow=0, volatility=10))
    sig = await a.logic(MarketData(price=0.99, lp_depth=60_000, meme_hype=60, whale_inflow=0, volatility=10))
    assert sig.action == "BUY"


@pytest.mark.asyncio
async def test_johan_hold_override():
    a = JohanAgent()
    md = MarketData(price=1, lp_depth=1_000, meme_hype=95, whale_inflow=0, volatility=10)
    sig = await a.logic(md)
    assert sig.action == "HOLD" and sig.confidence > 0.9


@pytest.mark.asyncio
async def test_genghis_buy():
    a = GenghisAgent()
    md = MarketData(price=1, lp_depth=1_000, meme_hype=70, whale_inflow=1_500, volatility=15)
    sig = await a.logic(md)
    assert sig.action == "BUY"
