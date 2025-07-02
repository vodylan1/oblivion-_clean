"""
pipelines.position_manager
Phase 7-5 ledger logic  ➜  Phase 11-B risk-sizing adapter

• Keeps all live positions in ``PositionManager.open_positions`` (id → record)
• Persists to storage/positions.json so state survives restarts
• Exposes ``get_open_positions_usd()`` for risk sizing without a RiskManager import
"""

from __future__ import annotations

import json
import time
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List

# ──────────────────────────────────────────────────────────────────────────
_STORAGE = Path(__file__).parent.parent / "storage"
_STORAGE.mkdir(exist_ok=True)
_LEDGER = _STORAGE / "positions.json"  # single source of truth


class _PositionManager:
    """
    Internal singleton that tracks open / closed positions.
    Each *position* may be a lightweight object or a dict but MUST expose
    ``notional_usd`` either as an attribute or a key so the risk shim can sum it.
    """

    def __init__(self) -> None:
        self.open_positions: Dict[str, Any] = {}  # id → position (live)
        self._history: List[Dict[str, Any]] = []  # closed ledger
        self._load()

    # ───────── persistence helpers ───────────────────────────────────────
    def _load(self) -> None:
        if not _LEDGER.exists():
            return
        try:
            data = json.loads(_LEDGER.read_text())
            self.open_positions = data.get("open_positions", {})
            self._history = data.get("history", [])
            print(
                f"[PositionManager] Restored {len(self.open_positions)} open positions."
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[PositionManager] Corrupt ledger – starting fresh ({exc})")

    def _flush(self) -> None:
        payload = {
            "open_positions": self.open_positions,
            "history": self._history,
        }
        _LEDGER.write_text(json.dumps(payload, indent=2))

    # ───────── public mutators ────────────────────────────────────────────
    def add_position(
        self,
        pos_id: str,
        size: float,
        entry_price: float,
        side: str = "LONG",
        extra: Dict[str, Any] | None = None,
    ) -> None:
        """Register a new live position (lightweight helper)."""
        rec: Dict[str, Any] = {
            "ts": time.time(),
            "side": side,
            "size": size,
            "entry_price": entry_price,
            "notional_usd": size * entry_price,
        }
        if extra:
            rec.update(extra)
        self.open_positions[pos_id] = rec
        self._flush()

    def close_position(self, pos_id: str, exit_price: float) -> None:
        """Close an existing position and archive it to history."""
        pos = self.open_positions.pop(pos_id, None)
        if not pos:
            return
        pnl = (exit_price - pos["entry_price"]) * pos["size"]
        rec = {**pos, "exit_price": exit_price, "pnl": pnl, "closed_ts": time.time()}
        self._history.append(rec)
        self._flush()

    # ───────── inspection helpers ────────────────────────────────────────
    def list_open(self) -> Dict[str, Any]:
        return self.open_positions

    def list_history(self, n: int = 5) -> List[Dict[str, Any]]:
        return self._history[-n:]


# ── exported singleton + wrapper ------------------------------------------
_PM_SINGLETON = _PositionManager()


class PositionManager:
    """Public façade so other modules can call `PositionManager.instance()`."""

    @staticmethod
    def instance() -> _PositionManager:  # noqa: D401
        return _PM_SINGLETON


def position_manager_init() -> None:
    print("[PositionManager] Online")


# ---------------------------------------------------------------------------#
def get_open_positions_usd() -> float:
    """
    Convenience façade for risk sizing:
    returns the notional value (USD) of **all** open positions.
    """
    pm = PositionManager.instance()

    def _extract_notional(obj: Any) -> Decimal:
        # attribute first, fallback to key
        if hasattr(obj, "notional_usd"):
            return Decimal(str(getattr(obj, "notional_usd")))
        return Decimal(str(obj.get("notional_usd", 0)))

    return float(sum(_extract_notional(p) for p in pm.open_positions.values()))


# Explicit star-import surface
__all__ = [
    "PositionManager",
    "position_manager_init",
    "get_open_positions_usd",
]
