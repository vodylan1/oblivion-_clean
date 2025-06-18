"""
Synergy Conductor – Phase‑11
"""

from __future__ import annotations
import asyncio, random
from typing import Dict, List, Optional, Tuple

from agents import Agent, TradeSignal
from core.risk_manager.manager import RiskManager
from strategies import load as load_strategy
from pipelines.helius_stream import helius_stream_task, get_next_tick

STRATEGY_PRIORITY = ["atomic_arb", "pepe_momentum", "whale_shadow", "stealth_exec"]


class SynergyConductor:
    def __init__(self, agents: List[Agent], risk_mgr: RiskManager, decay: float = 0.995):
        self._agents   = agents
        self._risk_mgr = risk_mgr
        self._decay    = decay

        self._strategies: Dict[str, object] = {n: load_strategy(n) for n in STRATEGY_PRIORITY}
        self._weights: Dict[Agent, float]   = {ag: 1.0 for ag in agents}
        self._tick_cnt = 0

    # legacy alias
    async def vote(self, market_tick: dict | None = None) -> TradeSignal | None:
        return await self.tick(market_tick)

    # ------------------------------------------------------------------ #
    async def tick(self, market_tick: dict | None = None) -> TradeSignal | None:
        market_tick = market_tick or {}

        # ---- Pass A: Trump‑Card strategies
        for name in STRATEGY_PRIORITY:
            strat = self._strategies[name]
            try:
                sig: Optional[TradeSignal] = await strat.decide(market_tick)
            except Exception as exc:
                print(f"[conductor] {name} error:", exc)
                sig = None
            if sig and self._risk_mgr.accept(sig):
                return sig

        # ---- Pass B: legacy agents
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

        # decay + random reward every 20 ticks
        self._tick_cnt += 1
        if self._tick_cnt % 20 == 0:
            for ag in self._weights:
                self._weights[ag] *= self._decay
            self._weights[random.choice(scored)[1]] += 0.1

        sig, _ = max(
            scored,
            key=lambda p: p[0].confidence * self._weights.get(p[1], 1.0),
        )
        return sig

    # ------------------------------------------------------------------ #
    async def run_forever(self, delay: float = 0.4) -> None:
        asyncio.create_task(helius_stream_task())
        while True:
            try:
                market_tick = await asyncio.wait_for(get_next_tick(), timeout=delay)
            except asyncio.TimeoutError:
                market_tick = {}
            await self.tick(market_tick)
