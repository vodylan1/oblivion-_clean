"""
main.py
────────────────────────────────────────────────────────────────────────────
Phase-8-C (Birdeye feeds online)

Features
• Spot-trading demo loop (mock / devnet / mainnet)
• DerivativesEngine scaffold
• Mutation-Engine & Meme-Scanner (Birdeye trending)
• ExecutionEngine selects mode from --env flag
"""

from __future__ import annotations

import time
import argparse

# ─── Data & execution modules ──────────────────────────────────────────────
from pipelines.data_pipeline import data_pipeline_init, fetch_sol_price
from pipelines.execution_engine import (
    execution_engine_init,
    execute_trade,
)

# ─── Core / agent stack ────────────────────────────────────────────────────
from agents.synergy_conductor import (
    synergy_conductor_init,
    synergy_conductor_run,
)
from core.reflection_engine.reflection_engine import (
    reflection_engine_init,
    log_trade_outcome,
    analyze_history_and_trigger_patch,
    trade_history,
)
from core.patch_core.patch_core import patch_core_init, request_autopatch
from core.ego_core.ego_core import ego_core_init
from security.kill_switch import kill_switch_init, check_kill_switch_conditions

from core.concurrency_manager.concurrency_manager import (
    concurrency_manager_init,
    start_god_awareness_thread,
    latest_whale_alert,
)
from core.god_awareness.god_awareness import god_awareness_init

# ─── Phase-7 scaffolds ─────────────────────────────────────────────────────
from core.derivatives_engine.derivatives_engine import derivatives_engine_init
from pipelines.position_manager import position_manager_init, PM

# ─── Phase-8 stubs/feeds ───────────────────────────────────────────────────
from core.mutation_engine import mutation_engine_init, propose_patch
from intel.meme_scanner import meme_scanner_init, scan_feeds


# ───────────────────────────────────────────────────────────────────────────
def main(env: str = "mock", continuous: bool = False) -> None:
    """
    Entry-point.

    Parameters
    ----------
    env : {"mock", "devnet", "mainnet"}
        Determines how ExecutionEngine and DerivativesEngine behave.
    continuous : bool
        • False → run 3 demo cycles then exit
        • True  → loop forever
    """
    print("[Main] Starting Phase-8-C initialisation…")

    # ----- Phase-6 initialisers -------------------------------------------
    data_pipeline_init()
    execution_engine_init(env)          # NOTE: env passed through
    synergy_conductor_init()
    reflection_engine_init()
    patch_core_init()
    ego_core_init()
    kill_switch_init()
    god_awareness_init()
    concurrency_manager_init()

    # ----- Phase-7 scaffolds ----------------------------------------------
    derivatives_engine_init()
    position_manager_init()

    # ----- Phase-8 stubs ---------------------------------------------------
    mutation_engine_init()
    meme_scanner_init()

    # Background God-Awareness thread
    start_god_awareness_thread()

    emotional_state = "neutral"
    loop_count      = 0
    max_cycles      = float("inf") if continuous else 3

    print("[Main] Entering trading loop…")
    while loop_count < max_cycles:
        loop_count += 1
        print(f"\n[Main] Trade cycle #{loop_count}")

        # ── Market data ----------------------------------------------------
        market_data = fetch_sol_price()
        market_data.update(scan_feeds())        # meme_hype injected
        print(f"[Main] Market data: {market_data}")

        # Shift emotion if whale alert
        if latest_whale_alert["whale_alert"]:
            emotional_state = "fear"

        decision = synergy_conductor_run(market_data, emotional_state)
        print(f"[Main] Decision: {decision}")

        price = market_data.get("sol_price", 0.0)
        execute_trade(decision, price)

        # Mock PnL for reflection (until real fills wired)
        pnl = 5.0 if "BUY" in decision else -10.0
        log_trade_outcome(decision, price, pnl)

        if analyze_history_and_trigger_patch():
            request_autopatch()

        try:
            check_kill_switch_conditions(trade_history)
        except Exception as exc:
            print(f"[Main] {exc} – shutting down.")
            break

        time.sleep(3)

    print("[Main] Loop complete.")


# ───────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--env",
        choices=["mock", "devnet", "mainnet"],
        default="mock",
        help="Select execution environment",
    )
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Run indefinitely instead of 3 demo cycles",
    )
    args = parser.parse_args()

    main(env=args.env, continuous=args.continuous)
