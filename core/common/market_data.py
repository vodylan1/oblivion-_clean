"""
MarketData — canonical 5-field snapshot shared by agents, scorer, risk mgr.
"""
from pydantic import BaseModel

class MarketData(BaseModel):
    price: float          # last price (quote units)
    lp_depth: float       # pool depth USD
    meme_hype: int        # 0-100 sentiment
    whale_inflow: float   # whale buy vol (SOL)
    volatility: float     # σ %
