"""Canonical trade-side / signal / result dataclasses.

Placed at repo root so any package can simply `import trade_types` without
circular-import risk.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict


class TradeSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


@dataclass(frozen=True, slots=True)
class TradeSignal:
    """A strategy’s desired action before execution."""

    action: TradeSide            # BUY or SELL
    confidence: float            # 0-1 probability of edge
    meta: Dict[str, Any] = None  # arbitrary strategy hints


@dataclass(frozen=True, slots=True)
class TradeResult:
    """What actually happened on-chain (post-trade)."""

    ok: bool                       # was TX successful?
    usd_size: float                # notional size
    tx_hash: str | None = None     # blockchain TX ID
