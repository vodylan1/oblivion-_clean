"""
Synergy Conductor · Phase 11
────────────────────────────
• Queries high‑priority “Trump Card” strategies in strict priority order.
• Falls back to legacy agents (Phase 7/8) and keeps backward‑compat helpers
  such as `.vote()` and neutral HOLD fallbacks.
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
        agents: List[Any],                       # allow bare HoldAgent stubs
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

        # Pass A – high‑priority strategies
        for name in STRATEGY_PRIORITY:
            try:
                sig = await self._strategies[name].decide(market_tick)
            except Exception as exc:
                print(f"[conductor] {name} error:", exc)
                sig = None
            if sig and self._risk_mgr.accept(sig):
                return sig

        # Pass B – legacy / simple agents
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
            # Emit neutral placeholder so old tests & callers always get a signal
            return TradeSignal(action="HOLD", confidence=0.0, meta={})

        # safe scorer (legacy signals may lack .agent)
        def _score(sig: TradeSignal) -> float:
            agent_name = getattr(sig, "agent", "LEGACY")
            return sig.confidence * self._weights[agent_name]

        return max(signals, key=_score)

    # ────────────────────────────────────────────────────────────────
    def reward(self, agent_name: str, pnl_pct: float) -> None:
        self._weights[agent_name] = (
            self._weights[agent_name] * self._decay + pnl_pct * (1 - self._decay)
        )

    # back‑compat alias ------------------------------------------------
    async def vote(self, market_tick: dict | None = None) -> TradeSignal | None:
        return await self.tick(market_tick)

    # helper loop ------------------------------------------------------
    async def run_forever(self, delay: float = 0.4) -> None:
        while True:
            await self.tick({})
            await asyncio.sleep(delay)
