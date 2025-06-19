"""
Light‑weight, fire‑and‑forget Discord webhook helper.

Usage
-----
from notifications.discord_notifier import notify_discord, DiscordEmoji

notify_discord("Oblivion booting …", DiscordEmoji.GREEN_CIRCLE)
notify_discord("Critical error!",  DiscordEmoji.RED_CIRCLE)
"""
from __future__ import annotations

import os
import json
import asyncio
import aiohttp
from enum import Enum


class DiscordEmoji(str, Enum):
    GREEN_CIRCLE = "🟢"
    RED_CIRCLE = "🔴"
    ORANGE_CIRCLE = "🟠"
    BLUE_CIRCLE = "🔵"
    WHITE_CIRCLE = "⚪️"
    WARNING = "⚠️"


WEBHOOK_URL: str | None = os.getenv("DISCORD_WEBHOOK_URL")


async def _send_async(message: str, emoji: DiscordEmoji) -> None:
    """Internal async dispatcher."""
    if WEBHOOK_URL is None:
        # Silent‑fail if no webhook configured – avoids crashing main loop
        print("[discord] WEBHOOK_URL not set – skipping message")
        return

    payload = {
        "content": f"{emoji.value} **{message}**",
        # Discord allows up to 4096 chars in content; keep it short
    }

    try:
        async with aiohttp.ClientSession() as sess:
            async with sess.post(WEBHOOK_URL, json=payload, timeout=5) as resp:
                if resp.status != 204:  # Discord returns 204 No Content on success
                    body = await resp.text()
                    print(f"[discord] webhook error {resp.status}: {body[:120]}")
    except Exception as exc:
        print(f"[discord] send failed:", exc)


def notify_discord(message: str, emoji: DiscordEmoji = DiscordEmoji.BLUE_CIRCLE) -> None:
    """
    Public entry point.  Non‑blocking – schedules the send on the current loop
    or spawns a fresh loop if none is running (CLI scripts).
    """
    coro = _send_async(message, emoji)

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No loop – run in a dedicated one so caller isn’t blocked.
        asyncio.run(coro)
    else:
        asyncio.create_task(coro)
