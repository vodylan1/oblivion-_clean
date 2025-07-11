"""Alpha‑Mesh mint‑stream stub (Phase‑6/7)."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import AsyncIterator, Optional


@dataclass(slots=True, frozen=True)
class MintEvent:
    mint: str
    owner: str
    slot: int


async def mint_stream(*, limit: Optional[int] = None) -> AsyncIterator[MintEvent]:
    """Async generator of mint events (deterministic CI stub).

    Always yields one fake event until the Helius WebSocket implementation
    lands in Phase‑8.
    """
    yield MintEvent(
        mint="So11111111111111111111111111111111111111112",
        owner="7X3F3…FAKE",
        slot=123_456_789,
    )
    return
