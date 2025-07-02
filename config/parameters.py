"""
Runtime-overrideable risk & misc settings.

Anything in parameter.json (singular) still works; we just add
two extra keys the new RiskManager facade expects.
"""

from __future__ import annotations

import json, pathlib
from decimal import Decimal

# -------- defaults required by risk pipeline -----------------------------
VAR_CAP_RATIO: float = 0.25  # 25 % of wallet is VaR cap for next trade
BUY_LOW_CONF: bool = False  # halve size when agent marks signal 'low_conf'

# -------- load overrides from the existing JSON file ---------------------
_json = pathlib.Path(__file__).with_name("parameter.json")
if _json.exists():
    try:
        _data: dict = json.loads(_json.read_text())
        # preserve any keys you already have
        globals().update(_data)
        # allow JSON to override the two new ones if present
        VAR_CAP_RATIO = float(_data.get("VAR_CAP_RATIO", VAR_CAP_RATIO))
        BUY_LOW_CONF = bool(_data.get("BUY_LOW_CONF", BUY_LOW_CONF))
    except Exception as e:  # noqa: BLE001
        # Don’t crash the app if someone drops a bad JSON file in prod.
        print(f"[config.parameters] bad json → using defaults: {e}")
