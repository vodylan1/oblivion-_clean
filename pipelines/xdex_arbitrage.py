"""
xdex_arbitrage.py
Phase 10.1 – Cross-DEX arb, real aggregator calls to Jupiter.
We pick a route if spread≥0.25%.
"""

import os
import requests
import math
import asyncio
import time

from pipelines.tip_auto_tuner import tip_auto_tuner
from pipelines.exec_mesh import send_swap_transaction
from notifications.discord_notifier import notify_discord

MIN_SPREAD_PCT = 0.25

async def xdex_arbitrage_main() -> None:
    """
    Called every ~5s in a loop, or however you prefer.
    We'll fetch a route from Jupiter: example USDC->SOL
    Then see if the best route is better than reference price by >=0.25%.
    If yes => do the swap.
    """
    # For simplicity, we do a single direction: USDC->SOL
    base_url = "https://quote-api.jup.ag/v6/quote"
    params = {
        "inputMint":  "FCqfQSujuPxy6V42UvafBhszGv6Zh26AJP3poacZxZV6",  # USDC (Wormhole)
        "outputMint": "So11111111111111111111111111111111111111112",  # wSOL
        "amount": 100_000_000,  # e.g. 100 USDC in decimal 6
        "slippageBps": 20,
    }
    try:
        resp = requests.get(base_url, params=params, timeout=3)
        resp.raise_for_status()
        data = resp.json()
        route_list = data.get("data", [])
        if not route_list:
            return
        best = route_list[0]  # highest outAmount
        inAmount = best["inAmount"]
        outAmount = best["outAmount"]
        # convert to float:  USDC has 6 decimals, SOL has 9
        out_sol = outAmount / 1e9
        in_usdc = inAmount / 1e6

        # reference price?  let's assume 1 SOL ~ 20.0 USDC from some known feed
        # naive approach
        ref_price = 20.0
        implied_price = in_usdc/out_sol if out_sol>0 else 9999
        spread_pct = (ref_price - implied_price)/implied_price * 100

        if spread_pct < MIN_SPREAD_PCT:
            return

        # proceed with the trade
        lamports_per_cu = tip_auto_tuner.get_tip_lamports()
        await send_swap_transaction("USDC->SOL via Jupiter", 100.0, lamports_per_cu)
        await notify_discord(f"🟢 ARB trade => usdc->sol spread={spread_pct:.2f}%")
    except Exception as exc:
        print("[xdex_arbitrage] error:", exc)
