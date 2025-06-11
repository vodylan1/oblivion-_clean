"""Kill‑Switch export shim (Phase 10.1)."""
from .service import KillSwitch, arm, is_armed, arm_timestamp, trip  # noqa: F401

__all__: list[str] = [
    "KillSwitch",
    "arm",
    "trip",
    "is_armed",
    "arm_timestamp",
]
