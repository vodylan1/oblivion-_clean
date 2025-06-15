from __future__ import annotations
import random
from agents import TradeSignal
from core.risk_manager.manager import RiskManager
import yaml, pathlib

PARAMS = yaml.safe_load((pathlib.Path("config") / "stealth_params.yaml").read_text())

class Strategy:
    """Utility strategy – only active when a large single‑wallet trade would exceed
    configured impact threshold.  Here we emit a SPLIT signal the Conductor will
    forward to splitter.py"""
    def __init__(self):
        self.risk_mgr = RiskManager.instance()

    async def decide(self, mkt_tick):
        desired = mkt_tick.get("intent_size_usd")
        if not desired:
            return None
        depth = mkt_tick.get("dex_depth_usd", 1e9)
        impact = desired / depth * 100   # %
        if impact >= PARAMS["max_impact_pct"]:
            parts = min(5, max(2, int(desired // PARAMS["chunk_usd"])))
            return TradeSignal(
                action="STEALTH_SPLIT",
                token=mkt_tick["token"],
                size_usd=desired,
                aux={"parts": parts, "jitter": random.random()},
                confidence=0.7,
            )
        return None
