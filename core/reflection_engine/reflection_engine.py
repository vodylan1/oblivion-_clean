"""
reflection_engine.py

REFLECTION_ENGINE module for Phase 3.
Collects trade outcomes, logs them, and checks for repeated mistakes 
or anomalies to potentially trigger PATCH_CORE.
"""

import os
import time

# A simple in-memory store for demonstration
# (In the future, might read/write from logs/reflection_logs.md)
trade_history = []

def reflection_engine_init():
    """Initialize REFLECTION_ENGINE (placeholder)."""
    print("[ReflectionEngine] Initialized.")

def log_trade_outcome(decision: str, sol_price: float, profit_loss: float = 0.0):
    """
    Log the outcome of a trade (or hold).
    For demonstration, we store in memory plus append to WAR_LOG or reflection_logs.
    """
    timestamp = time.time()
    outcome_record = {
        "timestamp": timestamp,
        "decision": decision,
        "sol_price": sol_price,
        "profit_loss": profit_loss
    }
    trade_history.append(outcome_record)

    # Append to logs/reflection_logs.md (just a quick example)
    logs_dir = os.path.join(os.path.dirname(__file__), "../../logs")
    reflection_log_path = os.path.join(logs_dir, "reflection_logs.md")

    with open(reflection_log_path, "a", encoding="utf-8") as f:
        f.write(f"Time: {timestamp}, Decision: {decision}, Price: {sol_price}, PnL: {profit_loss}\n")

def analyze_history_and_trigger_patch():
    """
    Check trade_history for repeated mistakes or triggers.
    If we find anomalies, call PATCH_CORE.
    For Phase 3, we'll do a simple check: 
    If we have 3 consecutive trades with negative profit_loss, we trigger a patch request.
    """
    if len(trade_history) < 3:
        return  # Not enough data to analyze

    # Check last 3 trades
    recent = trade_history[-3:]
    negative_streak = all(tr["profit_loss"] < 0 for tr in recent)

    if negative_streak:
        print("[ReflectionEngine] Detected 3-loss streak! Triggering PatchCore.")
        return True  # signal we want to patch
    return False
