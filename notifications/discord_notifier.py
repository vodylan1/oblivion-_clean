"""
discord_notifier.py
Single responsibility: push plain-text messages to Discord.

Usage:
    await notify_discord("⭕ trade filled 123 USDC → 4.9 SOL")
"""

from __future__ import annotations
import json, os, asyncio
import aiohttp
from pathlib import Path

# -------------------------------------------------------------------- helpers
def _load_webhook() -> str | None:
    # env wins → else config/secrets.json
    if os.getenv("DISCORD_WEBHOOK"):
        return os.getenv("DISCORD_WEBHOOK")
    secrets = Path("config/secrets.json")
    if secrets.exists():
        try:
            data = json.loads(secrets.read_text())
            return data.get("discord_webhook")
        except Exception:
            pass
    return None


_WEBHOOK: str | None = _load_webhook()

# -------------------------------------------------------------------- api
async def notify_discord(msg: str) -> None:
    """Fire-and-forget – never raises, logs on failure."""
    if not _WEBHOOK:
        return
    try:
        async with aiohttp.ClientSession() as sess:
            async with sess.post(_WEBHOOK, json={"content": msg}, timeout=5) as r:
                if r.status not in (200, 204):
                    print("[discord] HTTP", r.status, await r.text())
    except Exception as exc:
        print("[discord] exc:", exc)


# tiny self-test
if __name__ == "__main__":
    asyncio.run(notify_discord("✅ notifier self-test OK"))
