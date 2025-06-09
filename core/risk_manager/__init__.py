"""
core.risk_manager – package façade
==================================

Exports:
    • RiskManager (Phase‑9‑A, already implemented in manager.py)
    • AutoTuner / Sentinel utilities are imported *inside* RiskManager when
      required, but we re‑export nothing else here to keep surface tight.
"""

from .manager import RiskManager  # noqa: F401  (re‑export for external imports)
