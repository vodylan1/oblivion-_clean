"""
Synergy Conductor · Phase 11
────────────────────────────
• Queries high‑priority “Trump Card” strategies in strict order.
• Falls back to legacy agents while keeping backward‑compat with
  older HoldAgent stubs used in Phase‑7/8 unit‑tests.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Dict, List, Callable, Awaitable, Any

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
        agents: List[Any],                       # allow bare HoldAgent stubs
        risk_mgr: RiskManager | None = None,
        decay: float = 0.995,
    ) -> None:
        self._agents: List[Any] = agents
        self._risk_mgr: RiskManager = risk_mgr or RiskManager.instance()
        self._decay = decay
        self._weights: Dict[str, float] = defaultdict(lambda: 1.0)
        self._strategies: Dict[str, object] = {
            n: load_strategy(n) for n in STRATEGY_PRIORITY
        }

    # ──────────────────────────────────────────────────────────────────
    async def tick(self, market_tick: dict | None = None) -> TradeSignal | None:
        """Single polling step; returns the chosen TradeSignal (or None)."""
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

        # Pass B – legacy / simple agents
        signals: list[TradeSignal] = []
        for ag in self._agents:
            coro: Callable[[dict], Awaitable | None] | None = None
            if hasattr(ag, "tick"):
                coro = ag.tick          # modern async Agent
            elif hasattr(ag, "decide"):
                coro = ag.decide        # very old Agent API
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
            # Emit neutral placeholder so legacy tests always receive a signal
            return TradeSignal(action="HOLD", confidence=0.0, meta={})


        best = max(
            signals,
            key=lambda s: s.confidence * self._weights[s.agent],
        )
        return best

    # ──────────────────────────────────────────────────────────────────
    def reward(self, agent_name: str, pnl_pct: float) -> None:
        """EMA weight update from daily PnL callback."""
        self._weights[agent_name] = (
            self._weights[agent_name] * self._decay + pnl_pct * (1 - self._decay)
        )

    # ── Back‑compat alias for Phase‑7 tests ──────────────────────────
    async def vote(self, market_tick: dict | None = None) -> TradeSignal | None:
        """Alias kept for old unit‑tests; delegates to tick()."""
        return await self.tick(market_tick)

    # optional helper -------------------------------------------------
    async def run_forever(self, delay: float = 0.4) -> None:
        while True:
            await self.tick({})
            await asyncio.sleep(delay)
