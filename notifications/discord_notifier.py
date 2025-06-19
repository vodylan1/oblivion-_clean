# notifications/discord_notifier.py
"""
Tiny fire‑and‑forget Discord webhook helper.
Usage:
    from notifications.discord_notifier import notify_discord
    await notify_discord("🚀 Oblivion is live!")
"""
from __future__ import annotations
import os, aiohttp, asyncio, textwrap

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

async def _post(msg: str) -> None:
    if not WEBHOOK_URL:
        return                                  # silently ignore if unset
    content = textwrap.shorten(msg, width=1800, placeholder=" …")
    async with aiohttp.ClientSession() as sess:
        await sess.post(WEBHOOK_URL, json={"content": content})

def notify_discord(msg: str) -> None:
    """Thread‑safe entry point (creates its own task)."""
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        return
    loop.create_task(_post(msg))
