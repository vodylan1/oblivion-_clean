"""
core/mutation_engine package
────────────────────────────
Exposes two helpers so `main.py` can simply:

    from core.mutation_engine import mutation_engine_init, propose_patch
"""
from .mutation_engine import mutation_engine_init, propose_patch  # noqa: F401

__all__ = ["mutation_engine_init", "propose_patch"]
