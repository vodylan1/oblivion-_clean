"""
Kill‑Switch v2
────────────────────────────────────────────────────────────
• Central panic switch toggled by risk‑manager, God‑Awareness,
  or manual CLI.
"""

from __future__ import annotations

import asyncio
import time
from typing import Final

from notifications.discord_notifier import notify_discord

# ----------------------------------------------------------------─ state
_FROZEN: bool = False
_ARM_TS: float | None = None
_REASON: str | None = None
_LOCK: Final = asyncio.Lock()


# ----------------------------------------------------------------─ helpers
def is_armed() -> bool:
    return _FROZEN


def arm_timestamp() -> float | None:
    return _ARM_TS


async def arm() -> None:
    """Manually arm (freeze) – no reason."""
    await trip("manual‑arm")


async def trip(reason: str) -> None:  # noqa: D401
    """
    Freeze all trading.  *reason* recorded for telemetry / discord.
    Safe to call multiple times.
    """
    global _FROZEN, _ARM_TS, _REASON
    async with _LOCK:
        if _FROZEN:
            return
        _FROZEN = True
        _ARM_TS = time.time()
        _REASON = reason
    await notify_discord(f"🔴 **Kill‑Switch ARMED**  reason=`{reason}`")


def frozen() -> bool:  # backwards‑compat for tests
    return _FROZEN


# convenience alias expected by some legacy code
KillSwitch = type(
    "KillSwitch",
    (),
    {
        "trip": staticmethod(trip),
        "frozen": staticmethod(frozen),
        "arm_timestamp": staticmethod(arm_timestamp),
    },
)
