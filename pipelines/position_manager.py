# pipelines/position_manager.py
"""
position_manager.py   – Phase 7-5 (unchanged logic, re-export fixed)

Keeps a JSON ledger of open/closed positions under  storage/positions.json
so state survives restarts.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List

# ───────────────────────────────────────────────────────────────────────────
_STORAGE = Path(__file__).parent.parent / "storage"
_STORAGE.mkdir(exist_ok=True)
_LEDGER  = _STORAGE / "positions.json"       # single source of truth


class _PositionManager:
    def __init__(self) -> None:
        self._open: List[Dict[str, Any]] = []     # live positions
        self._hist: List[Dict[str, Any]] = []     # closed history
        self._load()

    # ───────── persistence helpers ────────────────────────────────────────
    def _load(self) -> None:
        if not _LEDGER.exists():
            return
        try:
            data: Dict[str, Any] = json.loads(_LEDGER.read_text())
            self._open = data.get("open", [])
            self._hist = data.get("history", [])
            print(f"[PositionManager] Restored {len(self._open)} open positions.")
        except Exception as exc:                       # noqa: BLE001
            print(f"[PositionManager] Corrupt ledger – starting fresh ({exc})")

    def _flush(self) -> None:
        payload = {"open": self._open, "history": self._hist}
        _LEDGER.write_text(json.dumps(payload, indent=2))

    # ───────── public API ─────────────────────────────────────────────────
    def open_long(self, size: float, entry_price: float, sig: str) -> None:
        rec = {
            "ts":    time.time(),
            "side":  "LONG",
            "size":  size,
            "entry": entry_price,
            "sig":   sig,
        }
        self._open.append(rec)
        self._flush()

    def close_long(self, exit_price: float, sig: str) -> None:
        if not self._open:
            return
        pos = self._open.pop()
        pnl = (exit_price - pos["entry"]) * pos["size"]
        rec = {**pos, "exit": exit_price, "pnl": pnl, "close_sig": sig}
        self._hist.append(rec)
        self._flush()

    # ───────── convenience inspection ─────────────────────────────────────
    def list_open(self) -> List[Dict[str, Any]]:
        return self._open

    def list_history(self, n: int = 5) -> List[Dict[str, Any]]:
        return self._hist[-n:]


# exported singleton and init banner
PM = _PositionManager()


def position_manager_init() -> None:
    print("[PositionManager] Online – Phase 7-5")


# make the public surface explicit
__all__ = ["PM", "position_manager_init"]
