"""
pipelines package – re-exports & legacy shims.
"""

from types import SimpleNamespace

# expose real submodules for auto-import discovery
from . import exec_mesh, xdex_arbitrage  # noqa: F401

# ---------------------------------------------------------------- legacy stub
def _noop(*_a, **_kw):
    return None


# very old tests import `pipelines.execution_engine`
execution_engine = SimpleNamespace(
    open_position=_noop,
    close_position=_noop,
    get_price=_noop,
)
