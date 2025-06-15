from __future__ import annotations
import asyncio, time, yaml, pathlib
from agents import TradeSignal
from core.risk_manager.manager import RiskManager

PARAMS = yaml.safe_load((pathlib.Path("config") / "arb_params.yaml").read_text())

class Strategy:
    """Cross‑DEX atomic arbitrage using Jito bundle‑simulation.

    Implementation here is *minimal*: it only emits a TradeSignal object when
    a price‑spread mock function exceeds the tier threshold.
    """

    def __init__(self):
        self.risk_mgr = RiskManager.instance()
        self.last_ts = 0.0            # simple throttle

    async def decide(self, mkt_tick) -> TradeSignal | None:
        tier = self.risk_mgr.capital_tier()
        thresh = PARAMS["tier_threshold"][tier]
        spread = mkt_tick.get("mock_spread_bps", 0)        # produced by tests

        if spread > thresh and time.time() - self.last_ts > 0.25:
            self.last_ts = time.time()
            size = self.risk_mgr.position_limit_usd() * 0.1
            return TradeSignal(
                action="ATOMIC_ARB",
                token=mkt_tick["token"],
                size_usd=size,
                aux={"spread": spread},
                confidence=0.9,
            )
        return None
