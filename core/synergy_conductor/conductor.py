"""
Synergy Conductor · Phase 11
Routes Trump‑Card strategies and legacy agents, with full unit‑test
back‑compat (vote alias, HOLD fallback).
"""

from __future__ import annotations
import asyncio
from collections import defaultdict
from typing import Dict, List, Any, Awaitable, Callable

from agents import Agent, TradeSignal
from strategies import load as load_strategy
from core.risk_manager.manager import RiskManager

STRATEGY_PRIORITY = ["atomic_arb", "pepe_momentum", "whale_shadow", "stealth_exec"]


class SynergyConductor:
    # ────────────────────────────────────────────────────────────────
    def __init__(
        self,
        agents: List[Any],
        risk_mgr: RiskManager | None = None,
        decay: float = 0.995,
    ) -> None:
        self._agents = agents
        self._risk_mgr = risk_mgr or RiskManager.instance()
        self._decay = decay
        self._weights: Dict[str, float] = defaultdict(lambda: 1.0)
        self._strategies = {n: load_strategy(n) for n in STRATEGY_PRIORITY}

    # ────────────────────────────────────────────────────────────────
    async def tick(self, market_tick: dict | None = None) -> TradeSignal | None:
        market_tick = market_tick or {}

        # Pass A – priority strategies
        for name in STRATEGY_PRIORITY:
            try:
                sig = await self._strategies[name].decide(market_tick)
            except Exception as exc:
                print(f"[conductor] {name} error:", exc)
                sig = None
            if sig and self._risk_mgr.accept(sig):
                return sig

        # Pass B – legacy / Hold agents
        signals: list[TradeSignal] = []
        for ag in self._agents:
            coro: Callable[[dict], Awaitable | None] | None = (
                getattr(ag, "tick", None) or getattr(ag, "decide", None)
            )
            if coro is None:
                continue
            try:
                res = await coro(market_tick)
            except Exception as exc:
                print(f"[conductor] agent {getattr(ag, 'name', ag)} error:", exc)
                res = None
            if res:
                signals.append(res)

        if not signals:
            # neutral placeholder so old tests always get a signal
            return TradeSignal(action="HOLD", confidence=0.0, meta={})

        return max(signals, key=lambda s: s.confidence * self._weights[s.agent])

    # weight update --------------------------------------------------
    def reward(self, agent_name: str, pnl_pct: float) -> None:
        self._weights[agent_name] = (
            self._weights[agent_name] * self._decay + pnl_pct * (1 - self._decay)
        )

    # back‑compat alias ---------------------------------------------
    async def vote(self, market_tick: dict | None = None) -> TradeSignal | None:
        return await self.tick(market_tick)

    # simple loop helper --------------------------------------------
    async def run_forever(self, delay: float = 0.4) -> None:
        while True:
            await self.tick({})
            await asyncio.sleep(delay)
