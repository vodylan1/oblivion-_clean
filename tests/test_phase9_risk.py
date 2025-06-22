# tests/test_phase9_risk.py
import pytest

from core.risk_manager.manager import RiskManager
from agents import TradeSignal
from core.kill_switch.service import KillSwitch


def test_bucket_cap():
    rm = RiskManager.instance()
    sig = TradeSignal(action="BUY", confidence=1.0, meta={"token": "XYZ"})
    assert rm.pre_trade(sig, rm.bucket_cap - 1)
    assert not rm.pre_trade(sig, rm.bucket_cap + 1)


@pytest.mark.asyncio
async def test_kill_switch_trip():
    assert KillSwitch.frozen() is False
    await KillSwitch.trip("unit‑test")
    assert KillSwitch.frozen() is True
