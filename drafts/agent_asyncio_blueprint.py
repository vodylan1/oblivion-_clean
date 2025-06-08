from pydantic import BaseModel
from typing import Literal, Optional, List
import asyncio
import random


class TradeSignal(BaseModel):
    side: Literal["buy", "sell", "hold"]


class MarketData(BaseModel):
    price: float
    fair_value: float


class Agent:
    """Base trading agent interface."""
    def __init__(self, name: str):
        self.name = name

    async def process(self, data: MarketData) -> Optional[TradeSignal]:
        """Process new market data and optionally return a trade signal."""
        return None


class MachiavelliAgent(Agent):
    """Agent that buys if price is significantly below fair value."""
    async def process(self, data: MarketData) -> Optional[TradeSignal]:
        # Buys when price is less than 95% of fair value
        if data.price < data.fair_value * 0.95:
            return TradeSignal(side="buy")
        return None


async def feed(agents: List[Agent], iterations: int = 100, interval: float = 0.1):
    """Simulate an async market data feed for the agents."""
    base_price = 100.0
    base_fv = 100.0
    for _ in range(iterations):
        price = base_price * (1 + random.uniform(-0.1, 0.1))
        fair_value = base_fv  # could vary over time or include randomness
        data = MarketData(price=price, fair_value=fair_value)
        # Dispatch data to all agents concurrently and gather results
        results = await asyncio.gather(*(agent.process(data) for agent in agents))
        for agent, signal in zip(agents, results):
            if signal:
                print(f"{agent.name} generated signal: {signal.side} at price {data.price:.2f}")
        await asyncio.sleep(interval)


async def main():
    # Initialize ten trading agents
    agents = [MachiavelliAgent(name=f"Agent{i}") for i in range(10)]
    await feed(agents, iterations=20, interval=0.5)


if __name__ == "__main__":
    asyncio.run(main())
