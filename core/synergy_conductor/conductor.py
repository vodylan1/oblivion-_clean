"""
Synergy Conductor · Phase 11
───────────────────────────
• Orchestrates high‑alpha strategy modules (“Trump Cards” + Pepe‑Mode)
• Falls back to blended agent‑signals when no priority strategy fires
• Keeps exponential‑decay performance weights for classic agents
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Dict, List

# ─── Local imports ──────────────────────────────────────────────────────────────
from agents import Agent, TradeSignal
from strategies import load as load_strategy
from core.risk_manager.manager import RiskManager

# Highest‑priority / most‑profitable modules are queried first
STRATEGY_PRIORITY: list[str] = [
    "atomic_arb",        # Phase 11 – bundle‑level MEV arb
    "pepe_momentum",     # Moon‑shot momentum logic
    "whale_shadow",      # Smart‑wallet follow / copy
    "stealth_exec",      # Multi‑wallet laddering for large sizes
    # ↓ anything after this line can be re‑ordered without changing meta
]

class SynergyConductor:
    """
    Top‑level orchestration hub.
    """

    # ──────────────────────────────────────────────────────────────────────────
    def __init__(
        self,
        agents: List[Agent],
        risk_mgr: RiskManager | None = None,
        decay: float = 0.995,
    ) -> None:
        self._agents: List[Agent] = agents
        self._risk_mgr: RiskManager = risk_mgr or RiskManager.instance()
        self._decay: float = decay                       # weight EMA factor
        self._weights: Dict[str, float] = defaultdict(lambda: 1.0)

        # Dynamically load every high‑alpha module once at start‑up
        self._strategies: Dict[str, object] = {
            name: load_strategy(name) for name in STRATEGY_PRIORITY
        }

    # ──────────────────────────────────────────────────────────────────────────
    async def tick(self, market_tick: dict | None = None) -> None:
        """
        Entry point called each slot / websocket update.
        • market_tick can contain order‑book, sentiment, etc.
        """
        # 1) High‑priority “Trump Card” scan
        sig = await self._decide(market_tick or {})
        if sig is None:
            return

        # 2) Risk‑manager final check & fire
        await self._risk_mgr.assess_and_maybe_fire(sig)

    # ──────────────────────────────────────────────────────────────────────────
    async def _decide(self, market_tick: dict) -> TradeSignal | None:
        """
        Returns best TradeSignal from either specialised strategy
        or classical blended agents.
        """
        # ── Pass A: specialised strategies in strict priority order ─────────
        for name in STRATEGY_PRIORITY:
            strat = self._strategies.get(name)
            if strat is None:
                continue
            try:
                sig: TradeSignal | None = await strat.decide(market_tick)
                if sig and self._risk_mgr.accept(sig):
                    return sig                       # fire immediately
            except Exception as exc:                 # never crash loop
                print(f"[conductor] {name} error:", exc)

        # ── Pass B: legacy multi‑agent blend (EMA‑weighted) ────────────────
        signals: list[TradeSignal] = []
        for agent in self._agents:
            try:
                s = await agent.tick(market_tick)
                if s:
                    signals.append(s)
            except Exception as exc:
                print(f"[conductor] agent {agent.name} error:", exc)

        if not signals:
            return None

        # Rank by confidence × performance weight
        ranked = sorted(
            signals,
            key=lambda s: s.confidence * self._weights[s.agent],
            reverse=True,
        )
        return ranked[0]

    # ──────────────────────────────────────────────────────────────────────────
    def reward(self, agent_name: str, pnl_pct: float) -> None:
        """
        Called by PnL callback to update agent weights (EMA).
        """
        self._weights[agent_name] = (
            self._weights[agent_name] * self._decay + pnl_pct * (1 - self._decay)
        )

    # optional convenience
    async def run_forever(self, poll_delay: float = 0.4) -> None:
        """
        Simple while‑True loop for quick local testing.
        In production you’ll likely be driven by websocket callbacks instead.
        """
        while True:
            await self.tick({})
            await asyncio.sleep(poll_delay)
