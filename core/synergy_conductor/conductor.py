"""
Synergy Conductor · Phase 11
────────────────────────────
Routes trade‑signals from high‑priority strategy modules
(Trump Cards + Pepe Mode) and classic agents, then passes
through the Risk‑Manager singleton.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Dict, List

from agents import Agent, TradeSignal
from strategies import load as load_strategy
from core.risk_manager.manager import RiskManager

STRATEGY_PRIORITY: list[str] = [
    "atomic_arb",
    "pepe_momentum",
    "whale_shadow",
    "stealth_exec",
]


class SynergyConductor:
    # ──────────────────────────────────────────────────────────────────
    def __init__(
        self,
        agents: List[Agent],
        risk_mgr: RiskManager | None = None,
        decay: float = 0.995,
    ) -> None:
        self._agents = agents
        self._risk_mgr: RiskManager = risk_mgr or RiskManager.instance()
        self._decay = decay
        self._weights: Dict[str, float] = defaultdict(lambda: 1.0)
        self._strategies: Dict[str, object] = {
            n: load_strategy(n) for n in STRATEGY_PRIORITY
        }

    # ──────────────────────────────────────────────────────────────────
    async def tick(self, market_tick: dict | None = None) -> TradeSignal | None:
        """Single polling step; returns the TradeSignal chosen (or None)."""
        market_tick = market_tick or {}

        # Pass A – high‑priority strategies
        for name in STRATEGY_PRIORITY:
            strat = self._strategies[name]
            try:
                sig = await strat.decide(market_tick)
            except Exception as exc:
                print(f"[conductor] {name} error:", exc)
                sig = None

            if sig and self._risk_mgr.accept(sig):
                return sig

        # Pass B – legacy agents
        signals: list[TradeSignal] = []
        for ag in self._agents:
            try:
                s = await ag.tick(market_tick)
            except Exception as exc:
                print(f"[conductor] agent {ag.name} error:", exc)
                s = None
            if s:
                signals.append(s)

        if not signals:
            return None

        # rank by confidence × EMA weight
        best = max(signals, key=lambda s: s.confidence * self._weights[s.agent])
        return best

    # ──────────────────────────────────────────────────────────────────
    def reward(self, agent_name: str, pnl_pct: float) -> None:
        """EMA weight update from daily PnL callback."""
        self._weights[agent_name] = (
            self._weights[agent_name] * self._decay + pnl_pct * (1 - self._decay)
        )

    # ── Back‑compat alias for older tests ────────────────────────────
    async def vote(self, market_tick: dict | None = None) -> TradeSignal | None:
        """Alias kept for Phase‑7 unit‑tests; delegates to tick()."""
        return await self.tick(market_tick)

    # optional helper -------------------------------------------------
    async def run_forever(self, delay: float = 0.4) -> None:
        while True:
            await self.tick({})
            await asyncio.sleep(delay)
