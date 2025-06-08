# core/synergy_conductor/conductor.py
"""
Oblivion – Synergy Conductor v1.3
• collects votes from enabled Agents
• applies dynamic Sharpe‑based weights
• overlays emotion (rage / fear) on confidence
• routes through RiskManager + Kill‑Switch v2
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List

from agents import Agent, TradeSignal
from core.ego_core.overlay import EmotionOverlay
from core.synergy_conductor.weighting import update_weights
from core.risk_manager.manager import RiskManager
from core.kill_switch.service import KillSwitch


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
        """
        Gather async votes and output a final TradeSignal.
        `market_data` must include key 'bucket_exposure_usd'
        so RiskManager can evaluate the projected exposure.
        """
        signals = await asyncio.gather(*(a.logic(market_data) for a in self.agents))

        score: Dict[str, float] = {}
        for sig in signals:
            w = self.weights.get(sig.meta.get("agent", ""), 1.0)
            score[sig.action] = score.get(sig.action, 0.0) + sig.confidence * w

        best_action = max(score, key=score.get)
        conf = score[best_action] / len(self.agents)

        # ───── Risk gate ─────
        projected_exposure = market_data.get("bucket_exposure_usd", 0.0)
        allowed = RiskManager.instance().pre_trade(
            TradeSignal(action=best_action, confidence=conf, meta={}), projected_exposure
        )
        if not allowed:
            await KillSwitch.trip("RiskManager veto")
            return TradeSignal(action="HOLD", confidence=0.0, meta={"reason": "risk‑veto"})

        # emotion overlay
        conf = self.emotion.apply(conf)

        # update weights every 20 cycles
        self._cycle += 1
        if self._cycle % 20 == 0:
            self.weights = update_weights(self.pnl_history)

        return TradeSignal(action=best_action, confidence=conf)
