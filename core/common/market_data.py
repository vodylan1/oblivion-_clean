"""
MarketData — canonical 5-field snapshot shared by agents, scorer, risk mgr.
"""
from pydantic import BaseModel


class MarketData(BaseModel):
    price: float          # last trade price
    lp_depth: float       # liquidity-pool depth in USD
    meme_hype: int        # 0-100 sentiment score
    whale_inflow: float   # recent whale buy volume (SOL)
    volatility: float     # σ in percent
