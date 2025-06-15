"""
Strategy registry façade
"""
from importlib import import_module
from functools import lru_cache

STRATEGY_PKGS = {
    "atomic_arb":        "strategies.atomic_arb.strategy",
    "pepe_momentum":     "strategies.pepe_mode.strategy",
    "whale_shadow":      "strategies.whale_shadow.strategy",
    "stealth_exec":      "strategies.stealth_exec.strategy",
}

@lru_cache(None)
def load(name: str):
    if name not in STRATEGY_PKGS:
        raise KeyError(f"unknown strategy {name}")
    return import_module(STRATEGY_PKGS[name]).Strategy()
