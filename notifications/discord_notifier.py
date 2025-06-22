"""
Lightweight Discord webhook helper (no external deps beyond `aiohttp`).
"""

import os, asyncio, json, datetime as _dt
from types import TracebackType
from typing import Any, Final, Optional

import aiohttp

_WEBHOOK: Final[str | None] = os.getenv("DISCORD_WEBHOOK_URL")


async def _post(payload: dict[str, Any]) -> None:
    """Internal: send JSON to the configured webhook, if any."""
    if _WEBHOOK is None:
        return  # silently ignore if webhook unset

    async with aiohttp.ClientSession(raise_for_status=True) as sess:
        try:
            await sess.post(_WEBHOOK, json=payload, timeout=5)
        except Exception:
            # swallow any network / rate‑limit errors; bot must stay alive
            pass


async def notify(
    content: str = "",
    *,
    embed_title: str | None = None,
    color: int = 0x2ECC71,
) -> None:
    """
    Send a Discord message.

    Parameters
    ----------
    content
        Plain text line (can be empty).
    embed_title
        If supplied, wraps `content` into a single‑field embed with this title.
    color
        Embed side‑bar colour (0xRRGGBB).
    """
    if _WEBHOOK is None:
        return

    payload: dict[str, Any]
    if embed_title:
        payload = {
            "embeds": [
                {
                    "title": embed_title,
                    "description": content or "\u200b",
                    "timestamp": _dt.datetime.utcnow().isoformat(),
                    "color": color,
                }
            ]
        }
    else:
        payload = {"content": content or "\u200b"}

    await _post(payload)


class _Lifecycle:
    """Async context‑manager for green / red lifecycle pings."""

    def __init__(self, service: str = "Oblivion"):
        self._svc = service

    async def __aenter__(self) -> None:  # noqa: D401
        await notify(f"{self._svc} **booting…**", embed_title="✅ Online")

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> bool:
        colour = 0xE74C3C if exc else 0x7289DA
        status = f"⚠️ Crash ({exc})" if exc else "🟥 Stopped"
        await notify("", embed_title=status, color=colour)
        # do not suppress exceptions
        return False


# Public helpers
lifecycle_notifier = _Lifecycle()  # to be used with `async with`
notify_discord = notify  # backward‑compat import path
