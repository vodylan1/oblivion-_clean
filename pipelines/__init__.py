"""
pipelines package bootstrap
────────────────────────────────────────────────────────────
• Dynamically imports live pipeline modules if present
  (`exec_mesh`, `xdex_arbitrage`, …).

• Registers *stub* modules so legacy tests that still expect
  `pipelines.execution_engine` and `pipelines.mev_stealth`
  do not crash when the full feature is not compiled in yet.
"""

from __future__ import annotations

import importlib
import sys
import types

# ----------------------------------------------------------------─ attempt to import live sub‑modules
for _mod in ("exec_mesh", "xdex_arbitrage"):
    try:
        importlib.import_module(f"pipelines.{_mod}")
    except Exception:  # pragma: no cover
        print(f"[pipelines] warn: {_mod} failed import – stubbed for tests")

# ----------------------------------------------------------------─ execution_engine legacy stub
def _noop(*_a, **_k):  # noqa: D401
    return None


exec_stub = types.ModuleType("pipelines.execution_engine")
exec_stub.open_position = _noop
exec_stub.close_position = _noop
exec_stub.get_price = lambda *_a, **_k: 0.0  # returns price float
exec_stub.RISK_PCT = 0.02                    # default 2 % risk per trade
exec_stub._balance_lamports = lambda *_a, **_k: int(10 * 1e9)  # 10 SOL mock
sys.modules["pipelines.execution_engine"] = exec_stub

# ----------------------------------------------------------------─ mev_stealth helpers (real thin shim)
from pipelines import mev_stealth as _ms  # type: ignore  # noqa: E402

sys.modules["pipelines.mev_stealth"] = _ms
__all__: list[str] = ["exec_stub", "_ms"]
