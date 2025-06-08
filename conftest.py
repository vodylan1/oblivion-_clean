"""
conftest.py – makes `import core.…` work inside isolated pytest sessions.

By appending the repository root to ``sys.path`` we ensure every
package/module under this tree can be imported during unit-tests,
regardless of the current working directory.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:          # idempotent
    sys.path.insert(0, str(REPO_ROOT))
