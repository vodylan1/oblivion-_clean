"""
Non‑blocking write queue for position‑ledger flushes.
Activate via EXPERIMENTAL_ASYNC_LEDGER=true
"""

import asyncio
import os
from pathlib import Path
from typing import Dict

_FLAG = os.getenv("EXPERIMENTAL_ASYNC_LEDGER", "false").lower() == "true"
LEDGER_FILE = Path("logs/position_ledger.ndjson")
_QUEUE: "asyncio.Queue[Dict]" | None = None


def enqueue(record: Dict):
    if not _FLAG:
        _write_sync(record)
        return
    global _QUEUE
    if _QUEUE is None:
        _QUEUE = asyncio.Queue()
        asyncio.create_task(_worker())
    _QUEUE.put_nowait(record)


def _write_sync(rec: Dict):
    LEDGER_FILE.parent.mkdir(parents=True, exist_ok=True)
    LEDGER_FILE.write_text((LEDGER_FILE.read_text() if LEDGER_FILE.exists() else "") + f"{rec}\n")


async def _worker():
    while True:
        rec = await _QUEUE.get()
        _write_sync(rec)
