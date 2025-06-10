"""
xdex_arbitrage.py
────────────────────────────────────────────────────────────────────────────
Phase 10 – Cross-DEX arb (Raydium ↔ Orca ↔ OpenBook).
Uses:
 • BirdeyePro for real-time quotes,
 • TipAutoTuner for dynamic priority fee,
 • Execution mesh (exec_mesh.py) to route final tx.

Min spread = 0.25%
"""

import os
from typing import Dict, Optional

import math
import asyncio
import random
import time

from pipelines.tip_auto_tuner import tip_auto_tuner
from pipelines.exec_mesh import send_swap_transaction
from core.scoring_engine.model import ScoringEngine

MIN_SPREAD_PCT = 0.25  # from 4o data, skip smaller
SLIP_BUFFER = 0.0015   # e.g. 0.15% slippage margin for each leg
EXEC_FEE_EST = 0.0003  # e.g. Jupiter aggregator overhead

async def xdex_arbitrage_main(quote_data: Dict[str, float]) -> None:
    """
    Called every ~3-5s with fresh aggregator quotes
    quote_data example:
      {
        "ray_bid":  99.80,
        "ray_ask":  100.20,
        "orca_bid": 100.00,
        "orca_ask": 100.30,
        ...
      }
    We look for spread >= 0.25% and do a small-size in-and-out.
    """
    # example simple RAY ↔ ORCA check
    ray_ask = quote_data.get("ray_ask")
    orca_bid = quote_data.get("orca_bid")
    if not ray_ask or not orca_bid:
        return

    spread_pct = (orca_bid - ray_ask) / ray_ask * 100
    if spread_pct < MIN_SPREAD_PCT:
        return  # skip

    # Check if expectedProfit >= fees
    # We'll do a 1 SOL or 1 token notional, your choice.
    notional = 100.0  # e.g. 100 USDC
    expectedProfit = (spread_pct / 100) * notional
    # approximate cost in fees
    #  - slip cost
    #  - aggregator overhead
    #  - tip cost is decided automatically by tip_auto_tuner
    totalFees = notional * SLIP_BUFFER + notional * EXEC_FEE_EST
    if expectedProfit < totalFees:
        return

    # if we pass checks, do the trade:
    lamports_per_cu = tip_auto_tuner.get_tip_lamports()
    await send_swap_transaction("RAY->ORCA", notional, lamports_per_cu)


