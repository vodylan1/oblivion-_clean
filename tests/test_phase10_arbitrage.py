"""
test_phase10_arbitrage.py
────────────────────────────────────────────────────────────────────────────
Minimal test for cross-DEX arb + tipAuto logic.
Use pytest -q tests/test_phase10_arbitrage.py
"""

import pytest
import asyncio

from pipelines.xdex_arbitrage import xdex_arbitrage_main
from pipelines.tip_auto_tuner import tip_auto_tuner


@pytest.mark.asyncio
async def test_xdex_spread():
    # feed some congestion data
    for _ in range(10):
        tip_auto_tuner.record_slot(
            accept_count=100, drop_count=10
        )  # 10% drop => ~ average ratio=0.09
    # => expects ~500 lamports/cU or 900 ?

    # minimal scenario
    quotes = {
        "ray_ask": 99.8,
        "orca_bid": 100.3,
    }
    # spread = (100.3 - 99.8)/99.8 => ~0.5%
    # enough to pass min 0.25% ?

    await xdex_arbitrage_main(quotes)
    # just ensure no crash
