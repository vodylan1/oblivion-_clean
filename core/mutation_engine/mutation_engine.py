"""
core/mutation_engine/mutation_engine.py
────────────────────────────────────────────────────────────────────────────
Phase-8 prototype
─────────────────
* Watches the last N trades (passed in from main.py)
* If recent PnL is poor it proposes a JSON “patch” (lower buy_threshold)
* Logs every proposal to  core/mutation_engine/patch_log.jsonl
* Fires a Discord notification so you see it in real time
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.notifier.notifier import notify

# ───────────────────────────────────────────────────────────────────────────
_PATCH_LOG = Path(__file__).resolve().parent / "patch_log.jsonl"


def mutation_engine_init() -> None:
    """Banner only – called once from main.py."""
    print("[MutationEngine] Online – prototype")


# -----------------------------------------------------------------------------
def _log_patch(sugg: Dict[str, Any]) -> None:
    """Append the suggestion as one JSON line for later analysis."""
    with _PATCH_LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(sugg) + "\n")


def propose_patch(history: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Very first heuristic:

    • Take last 5 trades.
    • If their **average** PnL < 0 → propose to drop `buy_threshold`
      (aggressive entry) by a step.

    Returns
    -------
    dict | None
        A JSON-serialisable suggestion or *None* if no action.
    """
    if len(history) < 5:  # not enough evidence?
        return None

    recent = history[-5:]
    avg_pnl = sum(t["profit_loss"] for t in recent) / 5

    if avg_pnl >= 0:
        return None  # performing fine

    # ---- compose suggestion -------------------------------------------------
    suggestion: Dict[str, Any] = {
        "ts": time.time(),
        "param": "buy_threshold",
        "new_value": 18 if avg_pnl < -10 else 20,
        "reason": f"avg PnL last 5 = {avg_pnl:.2f} USD",
    }

    # side-effects
    _log_patch(suggestion)
    notify(f"🛠️ **MutationEngine** proposal → ```json\n{json.dumps(suggestion)}```")

    return suggestion
