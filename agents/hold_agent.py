"""
Ultra‑light HOLD agent used only for bootstrapping / sanity‑checks.
It never emits trades; confidence is always 0.0.
"""

from __future__ import annotations
from typing import Any, Dict, Optional

from agents.base import TradeSignal


class HoldAgent:          # pylint: disable=too-few-public-methods
    name = "HOLD"

    async def tick(self, _: Dict[str, Any] | None = None) -> Optional[TradeSignal]:
        return TradeSignal(action="HOLD", confidence=0.0, meta={})
