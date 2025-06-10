import random

import numpy as np
import pytest
from core.risk_manager.auto_tuner import AutoTuner

pytestmark = pytest.mark.asyncio


async def test_auto_tuner_reduces_size_on_drawdown():
    tuner = AutoTuner.instance()
    # inject 96 synthetic hourly returns ~ N(-0.5%, 1%) to force DD
    rng = np.random.default_rng(42)
    for r in (rng.normal(-0.5, 1.0, 96)):
        tuner.update_pnl(float(r))
    sig = tuner.tune()
    assert sig.size_multiplier < 1.0
    assert sig.prio_fee_multiplier <= 1.0
