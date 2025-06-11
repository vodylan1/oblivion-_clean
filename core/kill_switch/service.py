"""
Kill-Switch v2
────────────────────────────────────────
* Functional API:  arm / is_armed / trip
* Legacy `KillSwitch` class so old code/tests still import it.
"""

from __future__ import annotations

import asyncio
import time
from typing import Final, Optional

_ARMED: bool = False
_ARM_TS: Optional[float] = None  # epoch seconds


# ───────────────────────────────────────────────────────── functional API
async def arm() -> None:
    """Arm the global kill-switch (trading frozen)."""
    global _ARMED, _ARM_TS
    _ARMED = True
    _ARM_TS = time.time()
    print("[KillSwitch] ‼️  ARMED  ‼️")
    # fire-and-forget Discord ping
    try:
        from notifications.discord_notifier import notify_discord
        await notify_discord("⚠️ **Kill-Switch ARMED** – trading halted")
    except Exception as exc:  # pragma: no cover
        print("[KillSwitch] discord err:", exc)


def is_armed() -> bool:
    return _ARMED


def arm_timestamp() -> Optional[float]:
    return _ARM_TS


async def trip() -> None:          # alias
    await arm()


# ───────────────────────────────────────────────────────── legacy shim
class KillSwitch:  # noqa: D101
    """Back-compat wrapper — do **not** use in new code."""

    @staticmethod
    async def arm() -> None:
        await trip()

    @staticmethod
    async def trip() -> None:
        await trip()

    @staticmethod
    def armed() -> bool:
        return is_armed()

    # legacy test expected `.frozen()`
    @staticmethod
    def frozen() -> bool:  # noqa: D401
        return is_armed()


# helper for idempotent awaits
async def _maybe_await(val):  # type: ignore
    if asyncio.iscoroutine(val):
        await val
