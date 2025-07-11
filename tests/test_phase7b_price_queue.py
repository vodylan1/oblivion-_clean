import asyncio
from pipelines.price_queue import price_stream, PriceSample


async def _collect():
    return [p async for p in price_stream(limit=3)]


def test_price_queue_ci_stub():
    samples = asyncio.run(_collect())
    assert len(samples) == 3
    assert all(isinstance(s, PriceSample) for s in samples)
    assert samples[0].solUsd == 125.0
