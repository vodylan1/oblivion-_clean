"""
Synergy Conductor – routes live market ticks through high‑priority strategies
and legacy agents, applies risk gating, and returns a TradeSignal.
"""

from __future__ import annotations
import asyncio, random
from importlib import import_module
from typing import Dict, List, Optional

from agents import Agent, TradeSignal
from core.risk_manager.manager import RiskManager
from strategies import load as load_strategy

from pipelines.helius_stream import helius_stream_task, get_next_tick

# ---------------------------------------------------------------------------

STRATEGY_PRIORITY = [
    "atomic_arb",
    "pepe_momentum",
    "whale_shadow",
    "stealth_exec",
]

# ---------------------------------------------------------------------------

class SynergyConductor:
    def __init__(
        self,
        agents: List[Agent],
        risk_mgr: RiskManager,
        decay: float = 0.995,
    ):
        self._agents     = agents
        self._risk_mgr   = risk_mgr
        self._decay      = decay

        self._strategies: Dict[str, object] = {
            name: load_strategy(name) for name in STRATEGY_PRIORITY
        }

        # weights for legacy‑agent voting
        self._weights: Dict[Agent, float] = {ag: 1.0 for ag in agents}
        self._tick_cnt = 0

    # ---------------------------------------------------------------------
    # compatibility: older tests call .vote(); alias to .tick()
    async def vote(self, market_tick: dict | None = None) -> TradeSignal | None:
        return await self.tick(market_tick)

    # ---------------------------------------------------------------------
    async def tick(self, market_tick: dict | None = None) -> TradeSignal | None:
        market_tick = market_tick or {}

        # ---- Pass A : high‑priority Trump‑Card strategies ----
        for name in STRATEGY_PRIORITY:
            strat = self._strategies[name]
            try:
                sig: Optional[TradeSignal] = await strat.decide(market_tick)
            except Exception as exc:
                print(f"[conductor] {name} error:", exc)
                sig = None

            if sig and self._risk_mgr.accept(sig):
                return sig

        # ---- Pass B : legacy agents ----
        signals: List[TradeSignal] = []
        for ag in self._agents:
            try:
                s = await ag.tick(market_tick)
            except Exception as exc:
                print(f"[conductor] agent error:", exc)
                continue
            if s:
                signals.append(s)

        if not signals:
            # emit neutral HOLD so downstream loggers have a signal object
            return TradeSignal(action="HOLD", confidence=0.0, meta={})

        # periodic weight decay + random reward
        self._tick_cnt += 1
        if self._tick_cnt % 20 == 0:
            for ag in self._weights:
                self._weights[ag] *= self._decay
            winner = random.choice(signals).agent
            self._weights[winner] += 0.1

        return max(signals, key=lambda s: s.confidence * self._weights.get(s.agent, 1.0))

    # ---------------------------------------------------------------------
    async def run_forever(self, delay: float = 0.4) -> None:
        """Main loop – pulls live ticks from Helius and routes through .tick()."""
        asyncio.create_task(helius_stream_task())   # background listener

        while True:
            try:
                market_tick = await asyncio.wait_for(get_next_tick(), timeout=delay)
            except asyncio.TimeoutError:
                market_tick = {}    # no fresh data within delay

            await self.tick(market_tick)
