"""
CLI wrapper that launches Oblivion with command‑line overrides.

Usage examples
--------------
$ python scripts/run_live.py                         # default RPC / relay
$ SOLANA_RPC=https://ssc-dao.genesysgo.net/ \
  python scripts/run_live.py --skip-bundles          # dry‑run without Jito
"""

from __future__ import annotations
import argparse, asyncio, os, sys, pathlib

# Ensure repo root is on import path when executed from sub‑dir
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import main                                             # noqa: E402
from notifications.discord_notifier import notify_discord  # ✅ Alert system

# ── argparse ------------------------------------------
p = argparse.ArgumentParser(description="Run Oblivion Phase 11 live loop")
p.add_argument("--skip-bundles", action="store_true",
               help="Disable Jito bundle submission (debug)")
p.add_argument("--delay", type=float, default=0.35,
               help="Polling delay seconds (default 0.35)")
args = p.parse_args()

# ── runtime flag injection ----------------------------
if args.skip_bundles:
    os.environ["OBLIVION_NO_BUNDLES"] = "1"

# ── main event loop ------------------------------------
async def _go() -> None:
    notify_discord("🟢 Oblivion booting …")  # ✅ Start-up ping
    await main.conductor.run_forever(delay=args.delay)

if __name__ == "__main__":
    try:
        asyncio.run(_go())
    except KeyboardInterrupt:
        notify_discord("🔴 Oblivion stopped by operator")  # ✅ Shutdown alert
