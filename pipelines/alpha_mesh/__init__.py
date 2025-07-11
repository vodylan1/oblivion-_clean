"""Alpha Data Mesh – Phase-6 scaffold."""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from typing import AsyncIterator, Final

__all__ = ["MintEvent", "mint_stream"]


@dataclass(frozen=True, slots=True)
class MintEvent:
    mint: str  # token address
    owner: str  # wallet that minted
    slot: int  # Solana slot number


_HELIUS_KEY: Final[str] = os.getenv("HELIUS_API_KEY")


async def mint_stream() -> AsyncIterator[MintEvent]:
    """Async generator of mint events.

    CI *or* missing API-key → emit ONE deterministic event and stop.
    Prod websocket wiring will land in Phase-6b.
    """
    if os.getenv("CI") or not _HELIUS_KEY:
        yield MintEvent(
            mint="So11111111111111111111111111111111111111112",
            owner="7X3F3…FAKE",
            slot=123_456_789,
        )
        return

    # 🟡 TODO: real Helius WS loop
    while True:  # placeholder to keep the coroutine alive
        await asyncio.sleep(60)
