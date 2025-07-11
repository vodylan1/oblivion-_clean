"""Price queue (Phase-7b).

* CI  -> emits N constant samples (no filesystem).
* Prod-> writes/reads a local SQLite ring-buffer (30 s cadence).
"""

from __future__ import annotations
import os, time, sqlite3, asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncIterator, Final, Optional

_DB: Final[Path] = Path(os.getenv("PRICE_DB", "price_queue.db"))
_SCHEMA = """create table if not exists price_queue(
  ts integer primary key,
  solUsd real,
  slot integer,
  source text
);"""


@dataclass(frozen=True, slots=True)
class PriceSample:
    ts: int
    solUsd: float
    slot: int
    source: str


# ── helpers ────────────────────────────────────────────────────────────────
def _init_db() -> None:
    if os.getenv("CI"):
        return  # no disk writes in CI
    conn = sqlite3.connect(_DB)
    conn.execute(_SCHEMA)
    conn.commit()
    conn.close()


_init_db()


async def writer(period: float = 30.0) -> None:  # used only in prod
    """Background task that appends a row every *period* seconds."""
    if os.getenv("CI"):
        return  # nothing to do in tests
    from pipelines.price_feed import sol_usd

    while True:
        now = int(time.time())
        price = sol_usd()
        slot = 0  # TODO: pull current slot from Helius when ready
        with sqlite3.connect(_DB) as c:
            c.execute(
                "insert or ignore into price_queue values (?,?,?,?)",
                (now, price, slot, "helius"),
            )
        await asyncio.sleep(period)


async def price_stream(limit: Optional[int] = None) -> AsyncIterator[PriceSample]:
    """Yield *limit* samples (or infinite if None).  CI path emits stubs."""
    if os.getenv("CI"):  # deterministic stub
        for i in range(limit or 0):
            yield PriceSample(
                ts=1_700_000_000 + i,
                solUsd=125.0,
                slot=123_456_000 + i,
                source="ci-stub",
            )
        return

    emitted = 0
    with sqlite3.connect(_DB) as c:
        c.row_factory = sqlite3.Row
        while limit is None or emitted < limit:
            row = c.execute(
                "select * from price_queue order by ts desc limit 1"
            ).fetchone()
            if row:
                yield PriceSample(**row)
                emitted += 1
            await asyncio.sleep(30)
