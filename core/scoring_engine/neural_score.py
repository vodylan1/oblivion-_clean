"""
neural_score.py  – Phase 8-B
Dynamic 0–100 score =  w_price·f(price) + w_meme·f(hype) + bias

Weights live in  config/neural_weights.json  so you can tune on the fly.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Final

from .scoring_engine import compute_score as price_score        # reuse
# ────────────────────────────────────────────────────────────────
_CFG_PATH: Final[Path] = Path(__file__).resolve().parents[2] / "config" / "neural_weights.json"
_DEFAULTS: Final[dict[str, float]] = {"w_price": 0.5, "w_meme": 0.5, "bias": 0.0}

_WEIGHTS: dict[str, float] | None = None     # lazy-loaded


def _load_weights() -> dict[str, float]:
    global _WEIGHTS
    if _WEIGHTS is not None:
        return _WEIGHTS                       # already cached

    try:
        data: dict[str, float] = json.loads(_CFG_PATH.read_text())
        _WEIGHTS = {**_DEFAULTS, **data}
        print(f"[NeuralScore] Weights loaded · {_WEIGHTS}")
    except FileNotFoundError:
        print("[NeuralScore] No weight file – using defaults")
        _WEIGHTS = _DEFAULTS
    except json.JSONDecodeError as err:
        print(f"[NeuralScore] Malformed weights – {err}; using defaults")
        _WEIGHTS = _DEFAULTS
    return _WEIGHTS


# ────────────────────────────────────────────────────────────────
def compute_score(market_data: dict) -> float:            # public API
    """
    Returns composite score ∈ [0, 100].
    Currently consumes:
        • sol_price   – classic price attractiveness curve
        • meme_hype   – Birdeye hype %, linearly scaled
    """
    w = _load_weights()

    price_part = price_score(market_data)                 # already 0-100
    hype_raw   = float(market_data.get("meme_hype", 0.0)) # 0-100
    hype_part  = max(0.0, min(100.0, hype_raw))

    score = w["w_price"] * price_part + w["w_meme"] * hype_part + w["bias"]
    # clamp
    return max(0.0, min(100.0, round(score, 2)))
