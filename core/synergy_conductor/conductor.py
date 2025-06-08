"""
Oblivion – Synergy Conductor v1.2
• collects votes from enabled Agents
• applies dynamic Sharpe‑based weights
• overlays emotion (rage / fear) on confidence
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List

from agents import Agent, TradeSignal
from core.ego_core.overlay import EmotionOverlay
from core.synergy_conductor.weighting import update_weights


class SynergyConductor:
    def __init__(self, agents: List[Agent], decay: float = 0.97):
        self.agents = [a for a in agents if a.meta.enabled]
        self.weights: Dict[str, float] = {a.meta.name: 1.0 for a in self.agents}
        self.decay = decay

        self.pnl_history: Dict[str, List[float]] = {a.meta.name: [] for a in self.agents}
        self.emotion = EmotionOverlay()
        self._cycle = 0

    # ──────────────────────────────────────────────

    async def vote(self, market_data: Dict[str, Any]) -> TradeSignal:
        """Gather async votes and output a final TradeSignal."""
        signals = await asyncio.gather(*(a.logic(market_data) for a in self.agents))

        score: Dict[str, float] = {}
        for sig in signals:
            w = self.weights.get(sig.meta.get("agent", ""), 1.0)
            score[sig.action] = score.get(sig.action, 0.0) + sig.confidence * w

        best_action = max(score, key=score.get)
        conf = score[best_action] / len(self.agents)

        # emotion overlay
        conf = self.emotion.apply(conf)

        # update weights every 20 cycles
        self._cycle += 1
        if self._cycle % 20 == 0:
            self.weights = update_weights(self.pnl_history)

        return TradeSignal(action=best_action, confidence=conf)
