"""
Strategy registry & lazy‑loader.

• STRATEGY_PKGS maps short names → import path of the class‐implementing file
• STRATEGY_PRIORITY is the polling order SynergyConductor will use
"""

from importlib import import_module
from functools  import lru_cache

# --------------------------------------------------------------------------- #
STRATEGY_PKGS = {
    "ping":           "strategies.ping.strategy",        # Phase 11‑b heartbeat
    "atomic_arb":     "strategies.atomic_arb.strategy",
    "pepe_momentum":  "strategies.pepe_momentum.strategy",
    "whale_shadow":   "strategies.whale_shadow.strategy",
    "stealth_exec":   "strategies.stealth_exec.strategy",
}

# Poll the always‑on heartbeat first, then the heavy strategies
STRATEGY_PRIORITY = [
    "ping",
    "atomic_arb",
    "pepe_momentum",
    "whale_shadow",
]

# --------------------------------------------------------------------------- #
@lru_cache(maxsize=None)
def load(name: str):
    """
    Lazy import & singleton‑instantiate a strategy.
    Example:  strat = load("ping")
    """
    if name not in STRATEGY_PKGS:
        raise KeyError(f"unknown strategy {name!r}")
    mod = import_module(STRATEGY_PKGS[name])
    return mod.Strategy()
