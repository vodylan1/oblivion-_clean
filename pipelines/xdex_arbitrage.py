"""
XDex two‑leg arbitrage (unit‑test stub).
"""

from __future__ import annotations
import requests, math, asyncio

from core.risk_manager.manager import RiskManager
from pipelines.exec_mesh import send_swap_transaction
from pipelines.signal_utils import latency_spread

# ── fallback tip‑tuner -------------------------------------------------
try:
    from core.risk_manager.auto_tuner import tip_auto_tuner  # real module
except ImportError:

    class _DummyTuner:  # minimal stub for tests
        def get_tip_lamports(self) -> int:
            return 500

        def record_slot(self, **kwds): ...

    tip_auto_tuner = _DummyTuner()

_risk_mgr = RiskManager.instance()
MIN_SPREAD_PCT = 0.25


async def xdex_arbitrage_main(quote_override: dict[str, float] | None = None) -> None:
    if quote_override:
        quote = quote_override
    else:
        resp = requests.get(
            "https://api.dexscreener.com/latest/dex/pairs/solana/raydium",
            timeout=3,
        )
        data = resp.json()["pairs"][0]
        quote = {
            "ray_ask": float(data["priceNative"]),
            "orca_bid": float(data["priceUsd"]),
        }

    spread_pct = latency_spread(quote["ray_ask"], quote["orca_bid"]) * 100
    if spread_pct < MIN_SPREAD_PCT:
        return

    lamports_per_cu = tip_auto_tuner.get_tip_lamports()
    size = math.floor(1 * 1e9)  # 1 SOL notional stub
    await send_swap_transaction("xdex‑arb", size, lamports_per_cu)
