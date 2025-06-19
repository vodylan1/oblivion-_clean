"""
Fire‑and‑forget Discord notifier.

notify_discord("text")  →  posts to the webhook if set.
Works both inside a running event‑loop (async) and
after KeyboardInterrupt when the loop is closed (sync fallback).
"""

from __future__ import annotations
import os, asyncio, textwrap, json, ssl, urllib.request

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")


async def _post_async(msg: str) -> None:
    import aiohttp

    content = textwrap.shorten(msg, width=1900, placeholder=" …")
    async with aiohttp.ClientSession() as sess:
        await sess.post(WEBHOOK_URL, json={"content": content})


def _post_sync(msg: str) -> None:
    """Last‑resort synchronous call used when event‑loop is already closed."""
    try:
        data = json.dumps({"content": textwrap.shorten(msg, 1900)}).encode()
        req = urllib.request.Request(WEBHOOK_URL, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        urllib.request.urlopen(req, context=ssl.create_default_context(), timeout=4)
    except Exception:
        pass  # swallow all – shutdown path


def notify_discord(msg: str) -> None:
    """Safe in any context – inside or after asyncio."""
    if not WEBHOOK_URL:
        return

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        _post_sync(msg)
        return

    if loop.is_closed():
        _post_sync(msg)
    else:
        loop.create_task(_post_async(msg))
