#!/usr/bin/env python
"""
Unified entrypoint for **Oblivion** live operation.

Usage
-----
python scripts/run_live.py              # full mode
python scripts/run_live.py --skip-bundles
python scripts/run_live.py --log-level DEBUG
"""

from __future__ import annotations

# --------------------------------------------------------------------------- #
# 0. Add project root to PYTHONPATH so `import main` always works
# --------------------------------------------------------------------------- #
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.resolve()))

# --------------------------------------------------------------------------- #
# 1. Standard library imports
# --------------------------------------------------------------------------- #
import asyncio
import argparse
import logging
import os
from importlib import import_module
from pathlib import Path

# --------------------------------------------------------------------------- #
# 2. Interpreter sanity-check (ensure venv active)
# --------------------------------------------------------------------------- #
_VENV_ROOT = Path(__file__).resolve().parent.parent / ".venv"
if _VENV_ROOT.exists() and _VENV_ROOT.name not in sys.executable:
    sys.stderr.write(
        f"[run_live] ERROR: Detected interpreter outside venv ⇒ {sys.executable}\n"
        "Activate the venv first:  source .venv/Scripts/activate\n"
    )
    sys.exit(1)

# --------------------------------------------------------------------------- #
# 3. CLI
# --------------------------------------------------------------------------- #
p = argparse.ArgumentParser()
p.add_argument(
    "--skip-bundles", action="store_true", help="Disable Jito bundle submits"
)
p.add_argument("--log-level", default="INFO", help="Root log level (DEBUG, INFO, …)")
args = p.parse_args()

logging.basicConfig(
    level=getattr(logging, args.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)

# --------------------------------------------------------------------------- #
# 4. Lazy imports (avoid circulars)
# --------------------------------------------------------------------------- #
# Import `start_background` but keep existing call-site name for minimal diff
from pipelines.jito_metrics import start_background as start_metrics_flusher

main = import_module("main")  # brings up `conductor`, etc.
from notifications.discord_notifier import lifecycle_notifier

# honour flag for metrics
if args.skip_bundles:
    os.environ["OBLIVION_DISABLE_BUNDLES"] = "1"


# --------------------------------------------------------------------------- #
# 5. Orchestrate
# --------------------------------------------------------------------------- #
async def _async_main() -> None:
    # start background metrics loop (runs forever)
    start_metrics_flusher()

    async with lifecycle_notifier:  # green on enter, red on exit
        await main.conductor.run_forever(delay=0.25)


if __name__ == "__main__":
    try:
        asyncio.run(_async_main())
    except KeyboardInterrupt:
        pass
