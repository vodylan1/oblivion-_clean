"""
pipelines package bootstrap
────────────────────────────────────────────────────────────
• Imports main live modules if available.
• Registers light stubs for legacy paths:
    pipelines.execution_engine
    pipelines.mev_stealth               (jitter / estimate_slippage)
"""

from __future__ import annotations

import importlib
import sys
import types

# ----------------------------------------------------------------─ try to import live modules
for _mod in ("exec_mesh", "xdex_arbitrage"):
    try:
        importlib.import_module(f"pipelines.{_mod}")
    except Exception:  # pragma: no cover
        print(f"[pipelines] warn: {_mod} failed import – using stub")

# ----------------------------------------------------------------─ execution_engine legacy stub
def _noop(*_a, **_k):  # noqa: D401
    return None


exec_stub = types.ModuleType("pipelines.execution_engine")
exec_stub.open_position = _noop
exec_stub.close_position = _noop
exec_stub.get_price = _noop
sys.modules["pipelines.execution_engine"] = exec_stub

# ----------------------------------------------------------------─ mev_stealth helpers (re‑export real impl)
from pipelines import mev_stealth as _ms  # type: ignore  # noqa: E402

sys.modules["pipelines.mev_stealth"] = _ms
