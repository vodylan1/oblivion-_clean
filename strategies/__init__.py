"""
Strategy registry & lazy‑loader.
"""

from importlib import import_module
from functools  import lru_cache

# --------------------------------------------------------------------------- #
STRATEGY_PKGS = {
    "ping":            "strategies.ping.strategy",          # Phase 11‑b
    "atomic_arb":      "strategies.atomic_arb.strategy",
    "pepe_momentum":   "strategies.pepe_mode.strategy",     # ← fixed path
    "whale_shadow":    "strategies.whale_shadow.strategy",
    "stealth_exec":    "strategies.stealth_exec.strategy",
}

STRATEGY_PRIORITY = [
    "ping",            # heartbeat first
    "atomic_arb",
    "pepe_momentum",
    "whale_shadow",
]

# --------------------------------------------------------------------------- #
@lru_cache(maxsize=None)
def load(name: str):
    if name not in STRATEGY_PKGS:
        raise KeyError(f"unknown strategy {name!r}")
    return import_module(STRATEGY_PKGS[name]).Strategy()
