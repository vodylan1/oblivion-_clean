"""Alpha‑Mesh mint‑stream stub (Phase‑6)."""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from typing import AsyncIterator, Final, Optional

__all__ = ["MintEvent", "mint_stream"]


@dataclass(frozen=True, slots=True)
class MintEvent:
    mint: str  # token address
    owner: str  # wallet that minted
    slot: int  # Solana slot number


_HELIUS_KEY: Final[str] = os.getenv("HELIUS_API_KEY")


async def mint_stream(*, limit: Optional[int] = None) -> AsyncIterator[MintEvent]:
    """Async generator of mint events (deterministic CI stub).

    Always yields one fake event.  Phase‑8 will replace this with a
    real Helius WebSocket implementation that streams live mints.
    """
    yield MintEvent(
        mint="So11111111111111111111111111111111111111112",
        owner="7X3F3…FAKE",
        slot=123_456_789,
    )
    if os.getenv("CI"):
        return

    # 🟡 TODO (Phase‑8): Connect to Helius WS and stream real events
    while True:  # pragma: no cover
        await asyncio.sleep(60)
