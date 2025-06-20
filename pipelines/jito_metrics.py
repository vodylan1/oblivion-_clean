"""
Flush bundle success/fail counters to Discord every 30 s.
"""

import asyncio, os
from notifications.discord_notifier import notify_discord
from pipelines.jito_submit import metrics

# ----------------------------------------------------------------------
# public helper for main.py
# ----------------------------------------------------------------------

_flusher_task: asyncio.Task | None = None

def start_background(loop: asyncio.AbstractEventLoop | None = None) -> None:
    """
    Launch the period‑flush coroutine exactly once.
    Called by main.py at import‑time.
    """
    global _flusher_task
    if _flusher_task and not _flusher_task.done():
        return  # already running

    loop = loop or asyncio.get_event_loop()
    _flusher_task = loop.create_task(_flusher())

# ----------------------------------------------------------------------

_WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL")
_INTERVAL = 30

async def _flusher():
    while True:
        ok, bad = metrics()
        if ok or bad:
            colour = 0x2ecc71 if ok else 0xe67e22
            await notify_discord(
                f"**Jito bundles** – ok {ok} / fail {bad}",
                colour=colour,
            )
        await asyncio.sleep(_INTERVAL)

_task: asyncio.Task | None = None

def ensure_running(loop: asyncio.AbstractEventLoop):
    global _task
    if _task is None:
        _task = loop.create_task(_flusher())
