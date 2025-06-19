"""
Fire‑and‑forget Discord notifier usable during runtime **and** on shutdown.
"""

from __future__ import annotations
import os, asyncio, textwrap, aiohttp

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL") or (
    "https://discord.com/api/webhooks/123456789012345678/AbCdEfGhIjKlMn"  # <‑‑ put real URL here or keep env‑var
)

async def _post_async(msg: str) -> None:
    """Single async HTTP POST via aiohttp."""
    content = textwrap.shorten(msg, width=1900, placeholder=" …")
    async with aiohttp.ClientSession() as sess:
        await sess.post(WEBHOOK_URL, json={"content": content}, timeout=4)

def notify_discord(msg: str) -> None:
    """Safe in any context – schedules task if loop alive, else runs one‑shot loop."""
    if not WEBHOOK_URL:
        return

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running loop → create one just for this post
        try:
            asyncio.run(_post_async(msg))
        except Exception:
            pass
        return

    if loop.is_closed():
        try:
            asyncio.run(_post_async(msg))
        except Exception:
            pass
    else:
        loop.create_task(_post_async(msg))
