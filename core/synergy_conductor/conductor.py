"""
Oblivion – Synergy Conductor v1.3
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Responsibilities
----------------
• Collect votes from *enabled* Agents (async)
• Apply Sharpe‑based weight drift (Phase‑7)
• Overlay emotion (rage / fear) confidence filter (Phase‑8)
• Route final order through Risk‑Sentinel / Auto‑Tuner (Phase‑9B)

Public API
----------
    async vote(market_data: dict) -> TradeSignal
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List

from agents import Agent, TradeSignal
from core.ego_core.overlay import EmotionOverlay
from core.synergy_conductor.weighting import update_weights
from core.risk_manager.sentinel import intercept  # NEW – Phase‑9B


class SynergyConductor:
    """Central lightweight vote aggregator."""

    def __init__(self, agents: List[Agent], decay: float = 0.97) -> None:
        self.agents = [a for a in agents if a.meta.enabled]
        self.weights: Dict[str, float] = {a.meta.name: 1.0 for a in self.agents}
        self.decay = decay

        self.pnl_history: Dict[str, List[float]] = {a.meta.name: [] for a in self.agents}
        self.emotion = EmotionOverlay()
        self._cycle = 0

    # ──────────────────────────────────────────────
    async def vote(self, market_data: Dict[str, Any]) -> TradeSignal:
        """
        Orchestrates one decision cycle:

        1. Gather async signals from every agent.
        2. Aggregate using per‑agent Sharpe weights.
        3. Apply emotion overlay.
        4. Feed the raw *TradeSignal → dict* through the Risk‑Sentinel
           (size & fee multipliers), then hydrate back to TradeSignal.
        """
        # 1 — gather
        signals = await asyncio.gather(*(a.logic(market_data) for a in self.agents))

        # 2 — weighted tally
        score: Dict[str, float] = {}
        for sig in signals:
            w = self.weights.get(sig.meta.get("agent", ""), 1.0)
            score[sig.action] = score.get(sig.action, 0.0) + sig.confidence * w

        best_action = max(score, key=score.get)
        conf = score[best_action] / len(self.agents)

        # 3 — emotion overlay
        conf = self.emotion.apply(conf)

        # 4 — risk pass‑through
        raw = TradeSignal(action=best_action, confidence=conf).model_dump()
        tuned = intercept(raw)  # Sentinel mutates size / fee fields if present
        # Convert back to dataclass instance if callers expect TradeSignal
        final = TradeSignal(**{k: tuned[k] for k in ("action", "confidence", "meta") if k in tuned})

        # weight refresh every 20 cycles
        self._cycle += 1
        if self._cycle % 20 == 0:
            self.weights = update_weights(self.pnl_history)

        return final
