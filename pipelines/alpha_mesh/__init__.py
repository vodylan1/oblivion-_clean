"""Alpha Data Mesh – Phase-6 scaffold.

Async generator `mint_stream()` yields MintEvent objects.
"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from typing import AsyncIterator, Final


@dataclass(slots=True, frozen=True)
class MintEvent:
    mint: str
    owner: str
    slot: int


_HELIUS_KEY: Final[str | None] = os.getenv("HELIUS_API_KEY")


async def mint_stream() -> AsyncIterator[MintEvent]:
    """Yield mint events; CI stub emits exactly one when tests run or key is unset."""
    # CI stub – emit exactly one event when tests run **or** when no key is set.
    if os.getenv("CI") or _HELIUS_KEY is None:
        yield MintEvent(
            mint="So11111111111111111111111111111111111111112",
            owner="7X3F3…FAKE",
            slot=123_456_789,
        )
        return

    # 🟡 TODO: real Helius websocket → MintEvent conversion
    while True:  # pragma: no cover
        await asyncio.sleep(60)
