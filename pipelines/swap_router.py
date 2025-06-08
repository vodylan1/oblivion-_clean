# pipelines/swap_router.py
"""
swap_router.py   · Phase 10-A
Thin wrapper around Jupiter v6 “swap (simulate)” endpoint.

Public helpers
--------------
simulate_buy(mint, amount_sol, slippage_bps=50)  -> dict
simulate_sell(mint, amount_sol, slippage_bps=50) -> dict
"""

from __future__ import annotations

import os
import time
from typing import Final, Literal

import requests

_SOL:   Final[str] = "So11111111111111111111111111111111111111112"
_USDC:  Final[str] = "Es9vMFrzaCER1z9vSbQx6ghEDcwcY9uCaNuS6dJP5SMi"

_JUP_URL: Final[str] = "https://quote-api.jup.ag/v6/swap"
_HEAD:    Final[dict[str, str]] = {"Content-Type": "application/json"}

# Optional – users who already have a *Jupiter* key can export it
_JUP_AUTH = os.getenv("JUPITER_AUTH_HEADER") or None
if _JUP_AUTH:
    _HEAD["Authorization"] = _JUP_AUTH


# ───────────────────────────────────────────────────────────────────────────
def _swap(
    side: Literal["buy", "sell"],
    in_mint: str,
    out_mint: str,
    lamports: int,
    slippage_bps: int,
) -> dict:
    """
    Internal helper.  Returns JSON from Jupiter or a dummy dict on no-op.
    """
    # Fast-path: identical mints → nothing to do, avoid 422
    if in_mint == out_mint:
        return {
            "simulated": True,
            "outAmount": lamports,
            "info": "same-mint no-op",
        }

    payload = {
        "simulate": True,                       # ← keep funds safe
        "inputMint":  in_mint,
        "outputMint": out_mint,
        "inAmount":   lamports,
        "slippageBps": slippage_bps,
        "swapMode":   "ExactIn",
        "onlyDirectRoutes": False,
    }

    r = requests.post(_JUP_URL, headers=_HEAD, json=payload, timeout=8)
    r.raise_for_status()
    data: dict = r.json()
    print(f"[SwapRouter] {side.upper()} simulation → out: {data['outAmount']}")
    return data


# ───────────────────────────────────────────────────────────────────────────
def simulate_buy(
    mint: str,
    amount_sol: float,
    slippage_bps: int = 50,
) -> dict:
    """
    Pretend to buy *mint* using amount_sol SOL.
    """
    lamports = int(amount_sol * 1_000_000_000)
    return _swap("buy", _SOL, mint, lamports, slippage_bps)


def simulate_sell(
    mint: str,
    amount_sol: float,
    slippage_bps: int = 50,
) -> dict:
    """
    Pretend to sell *mint* back to SOL.
    """
    lamports = int(amount_sol * 1_000_000_000)
    return _swap("sell", mint, _SOL, lamports, slippage_bps)
