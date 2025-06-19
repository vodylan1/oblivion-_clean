# notifications/discord_notifier.py
from __future__ import annotations
import os, asyncio, textwrap, aiohttp, sys

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")  # keep secrets out of git


async def _post(msg: str) -> None:
    data = {"content": textwrap.shorten(msg, 1900, placeholder=" …")}
    async with aiohttp.ClientSession() as sess:
        r = await sess.post(WEBHOOK_URL, json=data, timeout=4)
        if r.status >= 300:
            txt = await r.text()
            print(f"[discord] HTTP {r.status} – {txt}", file=sys.stderr)


def notify_discord(msg: str) -> None:
    if not WEBHOOK_URL:
        print("[discord] WEBHOOK url not set – alert skipped")
        return

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # outside event‑loop → send synchronously
        try:
            asyncio.run(_post(msg))
        except Exception as exc:
            print(f"[discord] post failed: {exc}", file=sys.stderr)
        return

    # inside live loop
    if loop.is_closed():
        try:
            asyncio.run(_post(msg))
        except Exception as exc:
            print(f"[discord] post failed: {exc}", file=sys.stderr)
    else:
        loop.create_task(_post(msg))
