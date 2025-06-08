"""
Pydantic MarketData model + stub async market feed (0.2 s cadence).
"""

from __future__ import annotations

import asyncio
from random import randint, uniform
from typing import AsyncIterator

from pydantic import BaseModel


class MarketData(BaseModel):
    price: float
    lp_depth: float          # total LP in SOL
    meme_hype: int           # 0‑100
    whale_inflow: float      # SOL in last block
    volatility: float        # σ over 1 h


class MarketFeed:
    def __aiter__(self) -> AsyncIterator[MarketData]:  # allows: async for md in MarketFeed()
        return self.data_stream()

    async def data_stream(self) -> AsyncIterator[MarketData]:
        while True:
            yield MarketData(
                price=uniform(0.01, 10.0),
                lp_depth=uniform(100, 500_000),
                meme_hype=randint(0, 100),
                whale_inflow=uniform(0, 2_000),
                volatility=uniform(0, 50),
            )
            await asyncio.sleep(0.2)
