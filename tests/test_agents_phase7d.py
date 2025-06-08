import pytest
from agents.nyx_agent import NyxAgent
from agents.inventor_agent import InventorAgent
from agents.johan_shadow_agent import JohanShadowAgent
from drafts.market_data import MarketData


@pytest.mark.asyncio
async def test_nyx_buy():
    md = MarketData(price=1, lp_depth=50_000, meme_hype=70, whale_inflow=0, volatility=30)
    sig = await NyxAgent().logic(md)
    assert sig.action == "BUY"


@pytest.mark.asyncio
async def test_inventor_low_conf_buy():
    md = MarketData(price=1, lp_depth=5_000, meme_hype=30, whale_inflow=0, volatility=10)
    sig = await InventorAgent().logic(md)
    assert sig.action == "BUY_LOW_CONF"


@pytest.mark.asyncio
async def test_shadow_buy_and_sell():
    agent = JohanShadowAgent()
    buy_md = MarketData(price=1, lp_depth=1_000, meme_hype=20, whale_inflow=0, volatility=10)
    sell_md = MarketData(price=1, lp_depth=1_000, meme_hype=60, whale_inflow=0, volatility=10)
    assert (await agent.logic(buy_md)).action == "BUY"
    assert (await agent.logic(sell_md)).action == "SELL"
