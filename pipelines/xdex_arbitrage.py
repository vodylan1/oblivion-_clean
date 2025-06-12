"""
xdex_arbitrage.py
Phase 10.2 – accepts injected quotes for unit‑test, uses RiskMgr size cap.
"""

import os
import requests
import asyncio
from typing import Dict, Optional

from pipelines.tip_auto_tuner import tip_auto_tuner
from pipelines.exec_mesh import send_swap_transaction
from notifications.discord_notifier import notify_discord
from core.risk_manager.manager import RiskManager

_risk_mgr = RiskManager()

MIN_SPREAD_PCT = 0.25


async def xdex_arbitrage_main(quote_override: Optional[Dict[str, float]] = None) -> None:
    """
    If `quote_override` supplied (unit‑tests) skip API call.
    """
    if quote_override:
        quote = quote_override
    else:
        base_url = "https://quote-api.jup.ag/v6/quote"
        params = {
            "inputMint": "FCqfQSujuPxy6V42UvafBhszGv6Zh26AJP3poacZxZV6",  # USDC
            "outputMint": "So11111111111111111111111111111111111111112",  # wSOL
            "amount": 100_000_000,  # 100 USDC
            "slippageBps": 20,
        }
        try:
            resp = requests.get(base_url, params=params, timeout=3)
            resp.raise_for_status()
            data = resp.json()["data"][0]
            quote = {"ray_ask": 1 / (data["outAmount"] / 1e9)}
        except Exception as e:
            print("[arb] quote err", e)
            return

    spread = ((quote["orca_bid"] - quote["ray_ask"]) / quote["ray_ask"]) * 100
    if spread < MIN_SPREAD_PCT:
        return

    lamports_per_cu = tip_auto_tuner.get_tip_lamports()
    size = _risk_mgr.position_limit_usd()
    await send_swap_transaction("USDC→SOL (XDex)", size, lamports_per_cu)
    await notify_discord(f"🟢 ARB fired spread={spread:.2f}% size=${size:,.0f}")
