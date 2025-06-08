"""
scoring_engine.py   ─── Phase 6 → refined in Phase 7
Compute a 0-100 attractiveness score based on current SOL price.

The curve:
* Peaks (≈100) near IDEAL_PRICE (default = 150 USD).
* Falls off linearly as price moves away.
"""

IDEAL_PRICE      = 150.0      # adjust whenever market regime changes
POINTS_PER_USD   = 0.5        # slope: 1 USD away subtracts 0.5 points
MIN_SCORE, MAX_SCORE = 0.0, 100.0


def scoring_engine_init() -> None:
    """No-op placeholder — kept for symmetry with other init() functions."""
    print("[ScoringEngine] Initialized.")


def compute_score(market_data: dict) -> float:
    """
    Return a float ∈ [0, 100]. Higher ⇒ more attractive to *buy*.
    """
    sol_price = float(market_data.get("sol_price", 0.0))

    distance   = abs(sol_price - IDEAL_PRICE)
    raw_score  = MAX_SCORE - distance * POINTS_PER_USD
    final_score = max(MIN_SCORE, min(MAX_SCORE, raw_score))

    return final_score
