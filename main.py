"""
main.py
Phase 10.1 – top-level script that runs:
   - background arbitrage loop (xdex_arbitrage_main)
   - background meme-snipe loop (meme_snipe_main)
   - optional synergy conductor logic
"""

import asyncio
import signal
import sys
from typing import Dict, Any

# background tasks
from pipelines.xdex_arbitrage import xdex_arbitrage_main
from pipelines.meme_snipe import meme_snipe_main

# synergy conductor (optional)
from agents.tywin_agent import TywinAgent
from agents.wick_agent import WickAgent
from core.synergy_conductor.conductor import SynergyConductor

# optional to gather real market_data for synergy logic
# from pipelines.some_real_feed import get_market_data_stub

_STOP_EVENT = asyncio.Event()

async def background_arbitrage_loop():
    """Call xdex_arbitrage_main every 5 seconds until stop."""
    while not _STOP_EVENT.is_set():
        try:
            await xdex_arbitrage_main()
        except Exception as e:
            print("[arbitrage_loop] Exception:", e)
        await asyncio.sleep(5)

async def background_meme_snipe_loop():
    """Call meme_snipe_main every 10 seconds until stop."""
    while not _STOP_EVENT.is_set():
        try:
            await meme_snipe_main()
        except Exception as e:
            print("[meme_snipe_loop] Exception:", e)
        await asyncio.sleep(10)

async def synergy_loop(conductor: SynergyConductor):
    """Optional synergy conductor loop. Could run every 4s or so."""
    while not _STOP_EVENT.is_set():
        try:
            # naive: fetch some real-time data or partial stub
            # e.g. market_data = get_market_data_stub()
            market_data: Dict[str, Any] = {}
            # synergy vote
            signal = await conductor.vote(market_data)
            # for demonstration, we just print:
            print("[synergy_loop] final decision:", signal.action, "conf=", signal.confidence)
        except Exception as e:
            print("[synergy_loop] Exception:", e)
        await asyncio.sleep(4)

async def main():
    # create synergy conductor if you want to run agent majority logic
    agents = [TywinAgent(), WickAgent()]
    conductor = SynergyConductor(agents=agents)
    
    # spawn background tasks
    tasks = []
    tasks.append(asyncio.create_task(background_arbitrage_loop()))
    tasks.append(asyncio.create_task(background_meme_snipe_loop()))
    tasks.append(asyncio.create_task(synergy_loop(conductor)))

    print("[main] Phase 10.1 loops started. Press Ctrl-C to stop.")
    # wait for a stop signal
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)
    for t in pending:
        t.cancel()

def _handle_sigint(sig, frame):
    print("[main] Received Ctrl-C. Stopping loops…")
    _STOP_EVENT.set()

if __name__ == "__main__":
    # handle Ctrl-C
    signal.signal(signal.SIGINT, _handle_sigint)
    # handle SIGTERM as well if you want graceful shutdown
    signal.signal(signal.SIGTERM, _handle_sigint)

    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("[main] Shutting down…")
        sys.exit(0)
