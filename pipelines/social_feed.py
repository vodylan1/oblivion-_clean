"""
Async stubs emitting social‑sentiment scores.
 Phase 8‑B uses random data; Phase 8‑C will connect real APIs.
"""

import asyncio
import random
from typing import AsyncIterator, Dict


async def social_stream() -> AsyncIterator[Dict[str, float]]:
    while True:
        yield {
            "telegram_hype": random.uniform(0, 100),
            "twitter_hype": random.uniform(0, 100),
            "google_trend": random.uniform(0, 100),
        }
        await asyncio.sleep(1)
