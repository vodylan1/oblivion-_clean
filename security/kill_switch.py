"""
kill_switch.py   · Phase 7-5
───────────────────────────────────────────────────────────────────────────────
Simple PnL-based kill switch.  When tripped we:

  • send a Discord alert via core.notifier
  • raise KillSwitchTripped so the caller can decide whether to exit,
    sleep-and-restart, or fall back to paper trading.

The helper never imports anything heavy so that it can be used from inside
tight loops without penalty.
"""

from __future__ import annotations

from typing import List, Dict

from core.notifier.notifier import notify


# ────────────────────────────────────────────────────────────────────────────
class KillSwitchTripped(RuntimeError):
    """Raised when catastrophic loss is detected."""


def kill_switch_init() -> None:
    print("[KillSwitch] Ready.")


def _last_n_pnl(trades: List[Dict], n: int = 5) -> float:
    """Return the summed PnL for the last *n* trades (or fewer)."""
    if not trades:
        return 0.0
    recent = trades[-n:]
    return sum(t["profit_loss"] for t in recent)


def check_kill_switch_conditions(trade_history: List[Dict]) -> None:
    """
    Inspect recent trade history and raise KillSwitchTripped if meltdown.

    •  total PnL of last 5 trades < –50 USD  ⇒  trip
    •  any single trade worse than –30 USD   ⇒  trip
    """
    if not trade_history:
        return

    total_recent = _last_n_pnl(trade_history, 5)
    worst_single = min(t["profit_loss"] for t in trade_history[-5:])

    if total_recent < -50 or worst_single < -30:
        msg = (
            "🚨 **KILL SWITCH** triggered  –  recent PnL:"
            f" {total_recent:.2f} USD  (worst {worst_single:.2f})"
        )
        notify(msg)  # Discord alert
        raise KillSwitchTripped(msg)
