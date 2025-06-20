"""
Synergy Conductor – Phase-11 (bootstrap mode)
Only the PingStrategy is polled until unfinished strategies are ready.
"""

from __future__ import annotations
import asyncio
from typing import Dict, List, Optional, Tuple

from agents import Agent, TradeSignal
from core.risk_manager.manager import RiskManager
from strategies import load as load_strategy

# ── Strategy registry ────────────────────────────────────────────────
# Keep heartbeat only; re-add others when implemented:
STRATEGY_PRIORITY = ["ping"]        # later: ["atomic_arb", "pepe_momentum", "whale_shadow", "ping"]

class SynergyConductor:
    def __init__(self, agents: List[Agent], risk_mgr: RiskManager, decay: float = 0.995):
        self._agents   = agents
        self._risk_mgr = risk_mgr
        self._decay    = decay

        self._strategies: Dict[str, object] = {n: load_strategy(n) for n in STRATEGY_PRIORITY}
        self._weights: Dict[Agent, float]   = {ag: 1.0 for ag in agents}
        self._tick_cnt = 0

    # -----------------------------------------------------------------
    async def vote(self, market_tick: dict | None = None) -> TradeSignal | None:
        return await self.tick(market_tick)

    async def tick(self, market_tick: dict | None = None) -> TradeSignal | None:
        market_tick = market_tick or {}

        # ---- Pass A: active strategies ---------------------------------
        for name, strat in self._strategies.items():
            try:
                sig: Optional[TradeSignal] = await strat.decide(market_tick)
            except Exception as exc:
                print(f"[conductor] {name} error:", exc)
                sig = None

            if sig and self._risk_mgr.accept(sig):
                return sig

        # ---- Pass B: legacy agents ------------------------------------
        scored: List[Tuple[TradeSignal, Agent]] = []
        for ag in self._agents:
            if not hasattr(ag, "tick"):
                continue
            try:
                sig = await ag.tick(market_tick)
            except Exception as exc:
                print("[conductor] agent error:", exc)
                continue
            if sig:
                scored.append((sig, ag))

        if not scored:
            return TradeSignal(action="HOLD", confidence=0.0, meta={})

        # simple weight/decay scheme
        self._tick_cnt += 1
        if self._tick_cnt % 20 == 0:
            for ag in self._weights:
                self._weights[ag] *= self._decay

        sig, _ = max(scored, key=lambda p: p[0].confidence * self._weights.get(p[1], 1.0))
        return sig

    # -----------------------------------------------------------------
    async def run_forever(self, delay: float = 0.4) -> None:
        while True:
            await self.tick({})
            await asyncio.sleep(delay)
