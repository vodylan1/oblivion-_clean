"""
Async stub emitting whale inflow (SOL) once per second.
Will be replaced by Helius websocket in Phase 8‑C.
"""

import asyncio
import random
from typing import AsyncIterator


async def whale_stream() -> AsyncIterator[float]:
    while True:
        yield random.uniform(0, 2_000)  # SOL
        await asyncio.sleep(1)
