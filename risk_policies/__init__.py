"""
Runtime‑pluggable capital‑at‑risk policies.

Public API
----------
get_max_exposure_usd(balance: Decimal, open_pos: Decimal) -> Decimal
"""
from __future__ import annotations

from decimal import Decimal
from functools import lru_cache
from importlib import import_module
from pathlib import Path
import json

_CFG = Path("config/risk_policy.json")
_DEFAULT = "risk_policies.static_25"          # dotted‑path to implementation


@lru_cache(maxsize=1)
def _impl():
    # hot‑load policy class at first call
    mod_name = _DEFAULT
    if _CFG.exists():
        try:
            mod_name = json.loads(_CFG.read_text())["policy"]
        except Exception:
            pass
    module = import_module(mod_name)
    return module.Policy()                    # must expose Policy class


def get_max_exposure_usd(balance: Decimal, open_pos: Decimal) -> Decimal:
    """
    Return the max **additional** USD we may allocate right now.

    Notes
    -----
    * Delegates to the currently‑selected Policy implementation.
    * Always returns Decimal ≥ 0.
    """
    addl = _impl().allowance(balance, open_pos)
    return max(Decimal("0"), addl)
