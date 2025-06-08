"""
Lightweight Discord notifier.
If DISCORD_WEBHOOK env var is absent, send() becomes a no‑op.
"""

import os
import aiohttp
import logging

WEBHOOK = os.getenv("DISCORD_WEBHOOK", "")


async def send(payload: dict):
    """POST payload to Discord webhook; silent if not configured."""
    if not WEBHOOK:
        return
    try:
        async with aiohttp.ClientSession() as sess:
            await sess.post(WEBHOOK, json=payload, timeout=5)
    except Exception as exc:
        logging.warning("Discord send failed: %s", exc)
