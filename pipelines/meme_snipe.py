"""
meme_snipe.py
────────────────────────────────────────────────────────────────────────────
Phase 10 – Meme pool-creation snipe logic.
Uses:
 • Meme-hype feed,
 • Helium/Helius webhook triggers,
 • TipAutoTuner for dynamic fees,
 • max slippage 15% (20% if hype≥90).
"""

import os
import asyncio
import random

from pipelines.tip_auto_tuner import tip_auto_tuner
from pipelines.exec_mesh import send_snipe_transaction

def calc_slippage(hype_score: float) -> float:
    slippage = 0.15
    if hype_score >= 90:
        slippage = 0.20
    return slippage

async def meme_snipe_on_pool_create(token_mint: str, hype_score: float, liquidity: float):
    """
    Called upon Helius webhook if a new pool is detected
    and 'token_mint' is recognized as a meme coin from filter.
    'hype_score': 0..100 from MemeScanner
    'liquidity': approximate initial liq in USD
    """
    # guard checks
    if liquidity < 2000:
        return  # too tiny
    max_slip = calc_slippage(hype_score)

    # decide notional, e.g. 300 USD
    notional = 300.0
    lamports_per_cu = tip_auto_tuner.get_tip_lamports()

    await send_snipe_transaction(token_mint, notional, max_slip, lamports_per_cu)
