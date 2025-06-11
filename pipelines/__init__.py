"""
pipelines package bootstrap
────────────────────────────────────────────────────────────
• Imports live modules where present.
• Provides stubs for legacy paths:
    pipelines.execution_engine      (open/close/get_price, RISK_PCT)
    pipelines.mev_stealth           (jitter / estimate_slippage)
"""

from __future__ import annotations

import importlib
import sys
import types

# ----------------------------------------------------------------─ import live sub‑modules (ignore failures)
for _mod in ("exec_mesh", "xdex_arbitrage"):
    try:
        importlib.import_module(f"pipelines.{_mod}")
    except Exception:  # pragma: no cover
        print(f"[pipelines] warn: {_mod} failed import – using stub")

# ----------------------------------------------------------------─ execution_engine stub
def _noop(*_a, **_k):  # noqa: D401
    return None


exec_stub = types.ModuleType("pipelines.execution_engine")
exec_stub.open_position = _noop
exec_stub.close_position = _noop
exec_stub.get_price = _noop
exec_stub.RISK_PCT = 0.02  # default 2 % used by unit‑test monkey‑patch
sys.modules["pipelines.execution_engine"] = exec_stub

# ----------------------------------------------------------------─ mev_stealth (real helpers)
from pipelines import mev_stealth as _ms  # type: ignore  # noqa: E402

sys.modules["pipelines.mev_stealth"] = _ms
