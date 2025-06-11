"""
Kill‑Switch v2
────────────────────────────────────────
* Functional API for new code (`arm`, `is_armed`, `trip`).
* Legacy `KillSwitch` class for older unit‑tests and CLI tooling.

State is kept in‑memory; prod deployment can swap to Redis / KV.
"""

from __future__ import annotations

import asyncio
import time
from typing import Final

# simple in‑process flag
_ARMED: bool = False
_ARM_TS: float | None = None  # epoch seconds

# --------------------------------------------------------------------------- functional
async def arm() -> None:
    """Arm the global kill‑switch."""
    global _ARMED, _ARM_TS
    _ARMED = True
    _ARM_TS = time.time()
    print("[KillSwitch] ‼️  ARMED  ‼️")
    # fire & forget Discord (no circular import)
    try:
        from notifications.discord_notifier import notify_discord  # late import
        await notify_discord("⚠️ **Kill‑Switch ARMED** – trading halted")
    except Exception as exc:  # pragma: no cover
        print("[KillSwitch] discord err:", exc)


def is_armed() -> bool:
    """Return True if the global switch is armed."""
    return _ARMED


def arm_timestamp() -> float | None:
    """Epoch seconds when switch was armed (or None)."""
    return _ARM_TS


# alias for compat with old test that calls `KillSwitch.trip()`
async def trip() -> None:  # noqa: D401
    await arm()


# --------------------------------------------------------------------------- legacy shim
class KillSwitch:  # noqa: D101
    ARMED: Final[bool] = False  # class‑level constant, not used

    # legacy code expected a `.arm()` **sync** method ⟹ redirect
    @staticmethod
    async def arm() -> None:  # noqa: D401
        await _maybe_await(arm())

    # some old modules called `.trip()` instead
    @staticmethod
    async def trip() -> None:  # noqa: D401
        await _maybe_await(trip())

    # and asked `.armed()` (note the past‑tense)
    @staticmethod
    def armed() -> bool:  # noqa: D401
        return is_armed()


# helper to await even if accidental double‑await
async def _maybe_await(coro):  # type: ignore
    if asyncio.iscoroutine(coro):
        await coro
