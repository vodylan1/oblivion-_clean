"""
signal_utils.py
--------------------------------------------------------
Utility helpers for alpha‑signal post‑processing
Phase 10.2 – adds latency‑decay on confidence.
"""

import math

# half‑life = 60 seconds → λ
_DECAY_LAMBDA = math.log(2) / 60.0


def decay_confidence(raw_conf: float, signal_age_sec: float) -> float:
    """Exponential decay; returns conf in [0,1]."""
    decayed = raw_conf * math.exp(-_DECAY_LAMBDA * max(signal_age_sec, 0))
    return max(0.0, min(1.0, decayed))
