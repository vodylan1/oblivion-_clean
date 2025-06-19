"""
Central metrics buffer for Jito bundle outcomes.
`record_ok()`            – call on HTTP 200
`record_fail(reason)`    – call on any non‑200
`start_background()`     – kicks off 60‑s flush loop
"""

from __future__ import annotations
import asyncio, collections, time
from notifications.discord_notifier import notify_discord

_OK:   int                           = 0
_FAIL: collections.Counter[str]      = collections.Counter()

async def _flusher(period: int = 60):
    global _OK, _FAIL
    while True:
        await asyncio.sleep(period)
        if not (_OK or _FAIL):
            continue

        lines = [f"📦 Jito bundles – last {period}s"]
        if _OK:
            lines.append(f"   ✅ success : {_OK}")
        for k, v in _FAIL.items():
            lines.append(f"   ❌ {k} : {v}")

        notify_discord("\n".join(lines))
        _OK, _FAIL = 0, collections.Counter()

def record_ok() -> None:
    global _OK
    _OK += 1

def record_fail(reason: str) -> None:
    _FAIL[reason] += 1

def start_background(loop: asyncio.AbstractEventLoop | None = None):
    (loop or asyncio.get_event_loop()).create_task(_flusher())
