#!/usr/bin/env python
"""
Entry point used during Phase‑11 soak‑tests.

* Boots SynergyConductor + Helius stream
* Optional `--skip-bundles` flag disables Jito submissions
* Emits Discord start/stop notifications
"""
from __future__ import annotations

import argparse
import asyncio
import signal
import sys
from pathlib import Path

# --- project imports ---------------------------------------------------------
# Ensure project root is on PYTHONPATH when executed as `python scripts/run_live.py`
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.synergy_conductor.conductor import SynergyConductor
from core.risk_manager.manager import RiskManager
from notifications.discord_notifier import notify_discord, DiscordEmoji
from agents.hold_agent import HoldAgent                     # ultra‑light stub
from pipelines.helius_stream import helius_stream_task
from pipelines.jito_metrics import start_metrics_flusher
from security.secure_wallet import sign_and_send

# --------------------------------------------------------------------------- #

parser = argparse.ArgumentParser(description="Run Oblivion live loop")
parser.add_argument("--skip-bundles", action="store_true",
                    help="Disable Jito bundle submission (dry‑run)")
parser.add_argument("--delay", type=float, default=0.25,
                    help="Loop sleep in seconds (default 0.25)")
args = parser.parse_args()

# --------------------------------------------------------------------------- #

risk_mgr = RiskManager.instance()
agents   = [HoldAgent()]                         # legacy agent pool
conductor = SynergyConductor(
    agents,
    risk_mgr=risk_mgr,
    enable_bundles=not args.skip_bundles,
    bundle_sender=sign_and_send,                 # dependency‑injector
)

# --- graceful shutdown ------------------------------------------------------ #
_shutdown_event = asyncio.Event()


def _on_signal(sig_name: str) -> None:
    print(f"[run_live] Caught {sig_name} – shutting down …")
    _shutdown_event.set()


# Register for Ctrl‑C / kill
signal.signal(signal.SIGINT,  lambda *_: _on_signal("SIGINT"))
signal.signal(signal.SIGTERM, lambda *_: _on_signal("SIGTERM"))


async def _main() -> None:
    notify_discord("Oblivion **booting** on mainnet", DiscordEmoji.GREEN_CIRCLE)

    # Fire‑and‑forget background tasks
    asyncio.create_task(helius_stream_task())
    asyncio.create_task(start_metrics_flusher())

    try:
        while not _shutdown_event.is_set():
            await conductor.tick({})
            await asyncio.sleep(args.delay)
    finally:
        notify_discord("Oblivion **stopped**", DiscordEmoji.RED_CIRCLE)


if __name__ == "__main__":
    asyncio.run(_main())
