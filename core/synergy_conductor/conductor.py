"""
Synergy Conductor – minimal bootstrap
Only the PingStrategy is queried until others are re‑enabled.
"""

from __future__ import annotations
import asyncio
from typing import Dict, List, Optional, Tuple

from agents import Agent, TradeSignal
from core.risk_manager.manager import RiskManager
from strategies import load as load_strategy

STRATEGY_PRIORITY = ["ping"]  # add more when ready


class SynergyConductor:
    def __init__(
        self, agents: List[Agent], risk_mgr: RiskManager, decay: float = 0.995
    ):
        self._agents = agents
        self._risk_mgr = risk_mgr
        self._decay = decay
        self._strategies = {n: load_strategy(n) for n in STRATEGY_PRIORITY}
        self._weights = {ag: 1.0 for ag in agents}
        self._tick_cnt = 0

    async def vote(self, tick: dict | None = None) -> TradeSignal | None:
        return await self.tick(tick)

    async def tick(self, tick: dict | None = None) -> TradeSignal | None:
        tick = tick or {}

        # pass A – strategies
        for name, strat in self._strategies.items():
            try:
                sig: Optional[TradeSignal] = await strat.decide(tick)
            except Exception as exc:
                print(f"[conductor] {name} error:", exc)
                sig = None
            if sig and self._risk_mgr.accept(sig):
                return sig

        # pass B – legacy agents (kept unchanged)
        scored: List[Tuple[TradeSignal, Agent]] = []
        for ag in self._agents:
            if not hasattr(ag, "tick"):
                continue
            try:
                sig = await ag.tick(tick)
            except Exception as exc:
                print("[conductor] agent error:", exc)
                continue
            if sig:
                scored.append((sig, ag))

        if not scored:
            return TradeSignal(action="HOLD", confidence=0.0, meta={})

        self._tick_cnt += 1
        if self._tick_cnt % 20 == 0:
            for ag in self._weights:
                self._weights[ag] *= self._decay

        sig, _ = max(
            scored, key=lambda p: p[0].confidence * self._weights.get(p[1], 1.0)
        )
        return sig

    async def run_forever(self, delay: float = 0.4) -> None:
        while True:
            await self.tick({})
            await asyncio.sleep(delay)
