"""
Machiavelli – stealthy early entry.

Logic:
• Buy if SCORING_ENGINE score ≥ 60 **and** price below 0.95 × IDEAL_PRICE.
• Otherwise hold.
"""

from core.scoring_engine.scoring_engine import compute_score, IDEAL_PRICE


def machiavelli_agent_logic(market_data: dict) -> str:
    score      = compute_score(market_data)
    sol_price  = market_data.get("sol_price", 0)

    if score >= 60 and sol_price < IDEAL_PRICE * 0.95:
        return "BUY"
    return "HOLD"
