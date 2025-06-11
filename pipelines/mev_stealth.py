"""
pipelines.mev_stealth
────────────────────────────────────────────────────────────
Light‑weight helper functions used by NyxAgent / InventorAgent
while the full MEV‑evasion module is still in development.
"""

import asyncio
import random

# ----------------------------------------------------------------─ public API
__all__: list[str] = ["jitter", "estimate_slippage"]


async def jitter(max_delay_ms: int = 200) -> None:
    """
    Async sleep random ± max_delay_ms/2  (default ±100 ms)
    to desync TX timing vs. sandwich bots.
    """
    if max_delay_ms <= 0:
        return
    delta = random.uniform(-max_delay_ms / 2, max_delay_ms / 2) / 1000.0
    await asyncio.sleep(max(0.0, max_delay_ms / 1000.0 + delta))


def estimate_slippage(size: float) -> float:  # noqa: D401
    """
    Toy linear slippage estimator used by InventorAgent tests.
    5 bps per 1 k USD notional.
    """
    return 0.0005 * (size / 1_000.0)
