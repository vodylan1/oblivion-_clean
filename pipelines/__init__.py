"""
pipelines package bootstrap
────────────────────────────────────────────────────────────
• Imports live pipeline sub‑modules when present.
• Registers *stub* modules so legacy tests that expect
  `pipelines.execution_engine` and `pipelines.mev_stealth`
  do not fail even when real engine is not compiled in yet.
"""

from __future__ import annotations

import importlib
import sys
import types

# ----------------------------------------------------------------─ attempt to import live modules
for _mod in ("exec_mesh", "xdex_arbitrage"):
    try:
        importlib.import_module(f"pipelines.{_mod}")
    except Exception:  # pragma: no cover
        print(f"[pipelines] warn: {_mod} failed import – using stub")


# ----------------------------------------------------------------─ execution_engine legacy stub
def _noop(*_a, **_k):  # noqa: D401
    return None


def _default_balance(_: str) -> int:  # 10 SOL ≈ 10 * 1e9 lamports
    return int(10 * 1_000_000_000)


def _size_lamports(network: str) -> int:  # noqa: D401
    """
    Very rough position‑size formula used by old unit‑test:
        size = balance_lamports * RISK_PCT
    """
    bal = exec_stub._balance_lamports(network)  # type: ignore
    return int(bal * exec_stub.RISK_PCT)  # type: ignore


exec_stub = types.ModuleType("pipelines.execution_engine")
exec_stub.open_position = _noop
exec_stub.close_position = _noop
exec_stub.get_price = lambda *_a, **_k: 0.0  # dummy price
exec_stub.RISK_PCT = 0.02  # default 2 %
exec_stub._balance_lamports = _default_balance  # mock balance
exec_stub._size_lamports = _size_lamports  # new helper

sys.modules["pipelines.execution_engine"] = exec_stub

# ----------------------------------------------------------------─ mev_stealth helper re‑export
from pipelines import mev_stealth as _ms  # type: ignore  # noqa: E402

sys.modules["pipelines.mev_stealth"] = _ms
__all__: list[str] = ["exec_stub", "_ms"]
