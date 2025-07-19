"""Choose between local ring‑buffer feed and Birdeye fallback."""
import asyncio, time
from oblivion.price_consumer.price_consumer import price_feed
from oblivion.price_consumer.birdeye_client import fetch_price
from oblivion.core.models import PriceSample
MAX_STALE_MS = 300

async def robust_price_feed():
    local_gen = price_feed()
    while True:
        try:
            sample = await asyncio.wait_for(local_gen.__anext__(), 0.1)
            if (time.time_ns() - sample.timestamp_ns)/1_000_000 <= MAX_STALE_MS:
                yield sample
                continue
        except Exception:
            pass  # fall through to API
        yield await fetch_price()
