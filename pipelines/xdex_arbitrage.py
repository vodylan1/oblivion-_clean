"""
xdex_arbitrage.py
──────────────────────────────────────────────────────────
Phase 10.1  – live cross-DEX arb.
• If *quotes* dict is supplied (unit-test) we skip HTTP.
• Otherwise we call Jupiter v6 public quote API (USDC ➜ wSOL).

A real production bot would loop over many pairs + amount sizes.
"""

from __future__ import annotations

import asyncio
import os
import random
import requests
from typing import Dict, Optional

from pipelines.exec_mesh import send_swap_transaction
from pipelines.tip_auto_tuner import tip_auto_tuner
from notifications.discord_notifier import notify_discord

USDC_MINT = "FCqfQSujuPxy6V42UvafBhszGv6Zh26AJP3poacZxZV6"   # Wormhole
WSOL_MINT = "So11111111111111111111111111111111111111112"

MIN_SPREAD_PCT = 0.25        # 0.25 % required before we fire
REF_PRICE_FALLBACK = 20.0    # USDC per SOL if no oracle feed yet


# ------------------------------------------------------------------------- helpers
def _fetch_jupiter_quote() -> Optional[Dict[str, float]]:
    """Call public Jupiter quote endpoint and return ask/bid for RAY/ORCA ex."""
    base = "https://quote-api.jup.ag/v6/quote"
    params = {
        "inputMint": USDC_MINT,
        "outputMint": WSOL_MINT,
        "amount": 100_000_000,          # 100 USDC
        "slippageBps": 20,
    }
    try:
        r = requests.get(base, params=params, timeout=3)
        r.raise_for_status()
        data = r.json().get("data", [])
        if not data:
            return None
        best = data[0]
        # naive: assume ask from Raydium, bid from Orca – in real life we’d parse route
        return {
            "ray_ask": best["inAmount"] / 1e6,   # price paid in USDC
            "orca_bid": best["outAmount"] / 1e9 * REF_PRICE_FALLBACK,
        }
    except Exception as exc:                     # pragma: no cover
        print("[xdex] quote error:", exc)
        return None


# … top of file unchanged …

async def xdex_arbitrage_main(
    quotes: Optional[Dict[str, float]] = None, *, _test: bool = False
) -> None:
    """
    If *quotes* supplied we’re in unit‑test mode.
    The extra *_test* flag suppresses real network calls when True.
    """
    if quotes is None:
        if _test:   # unit‑test asked not to hit network
            return
        quotes = _fetch_jupiter_quote()
        if quotes is None:
            return

    # rest of function unchanged …



# quick manual test
if __name__ == "__main__":  # pragma: no cover
    asyncio.run(xdex_arbitrage_main())
