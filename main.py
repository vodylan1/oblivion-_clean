"""
Oblivion · Phase 11 bootstrap
─────────────────────────────
Creates the global objects and starts the Synergy Conductor event‑loop.

Production wiring
-----------------
* RPC / WebSocket URLs come from environment variables for easy override.
* All “Trump Card” strategies are loaded automatically by the conductor.
* Legacy agents are optional; feel free to append more.

Unit‑tests import this file only for its top‑level symbols, **do not** start the
loop when pytest discovers the module.
"""

from __future__ import annotations
import asyncio, os

from core.synergy_conductor.conductor import SynergyConductor
from core.risk_manager.manager import RiskManager
from agents.tywin_agent import TywinAgent  # example legacy agent
from agents.hold_agent import HoldAgent  # ultra‑light agent stub
from pipelines.jito_metrics import start_background  # ✅ Add the flusher

# ── environment -----------------------------------------------------
RPC_URL = os.getenv("SOLANA_RPC", "https://api.mainnet-beta.solana.com")
WS_URL = os.getenv("SOLANA_WSS", "wss://api.mainnet-beta.solana.com")
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY", "")
JITO_RELAY_URL = os.getenv(
    "JITO_RELAY", "https://frankfurt.mainnet.block-engine.jito.wtf/api/v1/bundles"
)

# ── global singletons ----------------------------------------------
risk_mgr = RiskManager.instance()
agents = [TywinAgent(), HoldAgent()]
conductor = SynergyConductor(agents, risk_mgr=risk_mgr)
start_background()  # ✅ Launch the 60s metrics telemetry loop


# ── live runner -----------------------------------------------------
async def _run() -> None:
    """Start websockets + conductor loop."""
    print("▶ Oblivion Phase 11 booting …")

    # ‑‑ example: start Helius account‑change stream (non‑blocking) -------
    if HELIUS_API_KEY:
        from pipelines.helius_stream import run_helius_stream  # lazy‑import

        asyncio.create_task(run_helius_stream(HELIUS_API_KEY, WS_URL))

    # ‑‑ conductor forever loop -----------------------------------------
    await conductor.run_forever(delay=0.35)


if __name__ == "__main__":  # make sure pytest doesn’t execute the loop
    asyncio.run(_run())
