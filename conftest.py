"""
conftest.py – ensures project imports work inside isolated pytest sessions.

By appending the repository root to ``sys.path`` we make every package /
module under this tree importable during unit-tests, regardless of the
current working directory.
"""

from __future__ import annotations

# --------------------------------------------------------------------------
# Register the Solana stub *before* Pytest begins collecting tests.
import importlib

importlib.import_module("solana_stub")  # registers "solana.*" modules
# --------------------------------------------------------------------------

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:  # idempotent
    sys.path.insert(0, str(REPO_ROOT))
