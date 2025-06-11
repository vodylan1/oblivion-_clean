"""
Kill-Switch package re-exports and legacy shim.

`tests/test_phase9_risk.py` still expects a class `KillSwitch` with
`armed`/`arm()` semantics, so we wrap the v2 functional API.
"""
from __future__ import annotations
from .service import arm as _arm, is_armed as _is_armed

__all__: list[str] = ["KillSwitch", "arm", "is_armed"]

# functional re-export
arm = _arm
is_armed = _is_armed


class KillSwitch:  # legacy shim
    @staticmethod
    async def arm() -> None:  # noqa: D401
        await _arm()

    @staticmethod
    def armed() -> bool:  # noqa: D401
        return _is_armed()
