"""
Kill-Switch v2 – halts trading when cVaR or draw-down limits are breached.
"""

import asyncio
from typing import Callable, Awaitable

from notifications.discord_notifier import notify_discord

TRIP_LISTENERS: list[Callable[[], Awaitable[None]]] = []
_ARMED = False


def register_listener(cb: Callable[[], Awaitable[None]]) -> None:
    TRIP_LISTENERS.append(cb)


async def _fire_all() -> None:
    for cb in TRIP_LISTENERS:
        try:
            await cb()
        except Exception as exc:
            print("[KillSwitch] listener err:", exc)


async def arm() -> None:
    """Activate the global kill-switch."""
    global _ARMED
    if _ARMED:
        return
    _ARMED = True
    await notify_discord("⚠️ **Kill-Switch armed** – trading halted")
    await _fire_all()


def is_armed() -> bool:
    return _ARMED
