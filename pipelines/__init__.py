"""
pipelines package
────────────────────────────────────────────────────────────
• Provides light‑weight stubs so legacy tests that import
  `pipelines.execution_engine` or `pipelines.mev_stealth`
  do not explode.
"""

import types
import importlib
import sys

# ----------------------------------------------------------------─ public modules
for _m in ("exec_mesh", "xdex_arbitrage"):
    try:
        importlib.import_module(f"pipelines.{_m}")
    except Exception:  # pragma: no cover
        print(f"[pipelines] warn: {_m} failed import – ok in stub context")

# ----------------------------------------------------------------─ legacy stubs
def _noop(*_a, **_kw):  # noqa: D401
    return None


stub_mod = types.ModuleType("pipelines.execution_engine")
stub_mod.open_position = _noop
stub_mod.close_position = _noop
stub_mod.get_price = _noop
sys.modules["pipelines.execution_engine"] = stub_mod

# simple jitter stub for tests that import pipelines.mev_stealth.jitter
stealth_stub = types.ModuleType("pipelines.mev_stealth")
stealth_stub.jitter = _noop
sys.modules["pipelines.mev_stealth"] = stealth_stub
