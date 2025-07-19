"""Phase‑08: async price consumer reading SQLite ring‑buffer."""
import os, asyncio, aiosqlite, time
from typing import AsyncIterator
from oblivion.core.models import PriceSample
from oblivion.config import price_db_path, MAX_PRICE_AGE_MS

async def price_feed(*, poll_ms: int = 50) -> AsyncIterator[PriceSample]:
    db = await aiosqlite.connect(price_db_path(), uri=True)
    cursor = await db.cursor()
    while True:
        await cursor.execute("SELECT ts, price FROM queue ORDER BY ts DESC LIMIT 1;")
        row = await cursor.fetchone()
        if row:
            ts, price = row
            if (time.time_ns() - ts) / 1_000_000 <= MAX_PRICE_AGE_MS:
                yield PriceSample(timestamp_ns=ts, price=price)
        await asyncio.sleep(poll_ms / 1000)
