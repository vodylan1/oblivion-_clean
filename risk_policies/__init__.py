"""
Registry helper for dynamic import of risk-policy modules.
"""

from importlib import import_module

__all__: list[str] = ["load_policy"]  # <- export symbol so “from … import *” works


def load_policy(name: str = "static_25"):
    """
    Return the module implementing the named risk policy.

    Defaults to ``risk_policies.static_25``.
    """
    return import_module(f"risk_policies.{name}")
