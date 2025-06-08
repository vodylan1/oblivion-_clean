import pytest
from core.synergy_conductor.conductor import SynergyConductor
from agents.base import Agent, AgentMeta, TradeSignal


class HoldAgent(Agent):
    meta = AgentMeta(name="Hold", version="0.0", risk_profile="neutral", description="no‑op")

    async def logic(self, _):
        return TradeSignal(action="HOLD", confidence=1.0, meta={"agent": self.meta.name})


@pytest.mark.asyncio
async def test_live_cycle_40_ticks():
    conductor = SynergyConductor([HoldAgent()], decay=1.0)
    for _ in range(40):                     # run >20 to trigger weight refresh
        sig = await conductor.vote({})
        assert 0.0 <= sig.confidence <= 1.0
