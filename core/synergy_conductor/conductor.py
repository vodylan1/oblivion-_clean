"""
Synergy Conductor  v1.3 – now capital‑aware
"""

from __future__ import annotations
import asyncio
from typing import Any, Dict, List

from agents import Agent, TradeSignal
from core.ego_core.overlay import EmotionOverlay
from core.synergy_conductor.weighting import update_weights
from core.capital_manager.adaptive_strategy import apply_tier_overrides
from core.risk_manager.manager import RiskManager


class SynergyConductor:
    def __init__(self, agents: List[Agent], risk_mgr: RiskManager, decay: float = 0.97):
        self.agents = [a for a in agents if a.meta.enabled]
        self.weights: Dict[str, float] = {a.meta.name: 1.0 for a in self.agents}
        self.decay = decay

        self.pnl_history: Dict[str, List[float]] = {a.meta.name: [] for a in self.agents}
        self.emotion = EmotionOverlay()
        self.risk_mgr = risk_mgr
        self._cycle = 0

    # ──────────────────────────────────────────────
    async def vote(self, market_data: Dict[str, Any], signal_age: float = 0.0) -> TradeSignal:
        """Gather async votes and output a final TradeSignal."""
        signals = await asyncio.gather(*(a.logic(market_data) for a in self.agents))

        # apply latency decay to confidence
        from pipelines.signal_utils import decay_confidence
        for s in signals:
            s.confidence = decay_confidence(s.confidence, signal_age)

        score: Dict[str, float] = {}
        for sig in signals:
            w = self.weights.get(sig.meta.get("agent", ""), 1.0)
            score[sig.action] = score.get(sig.action, 0.0) + sig.confidence * w

        best_action = max(score, key=score.get)
        conf = score[best_action] / len(self.agents)

        # emotion overlay
        conf = self.emotion.apply(conf)

        # strategy overrides by capital tier (e.g. tighten slip, enlarge size)
        trade_params = apply_tier_overrides({}, self.risk_mgr.current_tier)

        # update weights every 20 cycles
        self._cycle += 1
        if self._cycle % 20 == 0:
            self.weights = update_weights(self.pnl_history)

        return TradeSignal(action=best_action,
                           confidence=conf,
                           meta=trade_params)
