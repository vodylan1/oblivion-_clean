import asyncio
import random


async def jitter(delay_ms: int = 200):
    """Sleep random ±delay_ms/2 to evade MEV timing prediction."""
    if delay_ms <= 0:
        return
    delta = random.uniform(-delay_ms / 2, delay_ms / 2) / 1000
    await asyncio.sleep(max(0, delay_ms / 1000 + delta))


def estimate_slippage(size: float) -> float:
    """Toy slippage model: 5 bps per 1 k size."""
    return 0.0005 * (size / 1_000)
