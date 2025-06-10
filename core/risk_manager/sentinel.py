"""
Sentinel – lightweight middleware that applies Auto‑Tuner hints
before orders are sent to the execution layer.
"""

from __future__ import annotations

from typing import Dict

from core.risk_manager.auto_tuner import AutoTuner

# Sentinel is intentionally stateless; the Conductor pipes every order dict
def intercept(order: Dict) -> Dict:
    tune = AutoTuner.instance().tune()

    order["max_size_usd"] *= tune.size_multiplier
    order["priority_fee"] *= tune.prio_fee_multiplier
    order.setdefault("meta", {})["auto_tune_note"] = tune.comment
    return order
