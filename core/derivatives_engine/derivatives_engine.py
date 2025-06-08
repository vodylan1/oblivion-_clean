"""
derivatives_engine.py  – Phase-7-5

 • Works on dev-net if `driftpy` ≥ 0.8 is import-able.
 • Falls back to a no-op stub so the rest of the stack never breaks.
"""

from __future__ import annotations

import time
from typing import Any, Dict

from solders.keypair import Keypair
from solana.rpc.api import Client

# ---------------------------------------------------------------------------
try:
    # driftpy ≥ 0.8.55 still uses AnchorPy Wallet
    from anchorpy import Wallet
    from driftpy.constants.config import devnet_config
    from driftpy.setup import DriftClient  # type: ignore
    _DRIFT_OK = True
except Exception as err:  # noqa: BLE001
    print(f"[DerivativesEngine] Drift not available, running in stub mode – {err}")
    _DRIFT_OK = False


# ---------------------------------------------------------------------------
class _RealDerivativesEngine:
    """Minimal wrapper around DriftClient (dev-net only)."""

    def __init__(self, cluster: str = "devnet") -> None:
        kp = Keypair()  # random throw-away dev-net wallet
        self.wallet = Wallet(kp)
        self.connection = Client("https://api.devnet.solana.com")
        self.client = DriftClient(self.connection, self.wallet, devnet_config())
        print("[DerivativesEngine] Online – cluster:", cluster)

    # ––– public trade helpers –––––––––––––––––––––––––––––––––––
    def open_long(self, market: int, size: float) -> str:  # returns sig
        sig = self.client.open_position(market_index=market, base_asset_amount=size)  # type: ignore
        print(f"[DerivativesEngine] LONG opened  mkt={market}  sz={size} → {sig}")
        return sig

    def close_long(self, market: int) -> str:
        sig = self.client.close_position(market_index=market)  # type: ignore
        print(f"[DerivativesEngine] LONG closed mkt={market} → {sig}")
        return sig


# ---------------------------------------------------------------------------
class _StubDerivativesEngine:  # identical interface, prints only
    def __init__(self, cluster: str = "devnet") -> None:
        self._note = f"[DerivativesEngine] Stub Online – cluster: {cluster}"
        print(self._note)

    def open_long(self, market: int, size: float) -> str:  # noqa: D401
        msg = f"[DerivativesEngine] (STUB) open_long  mkt={market}  sz={size}"
        print(msg)
        return "stub-sig"

    def close_long(self, market: int) -> str:
        msg = f"[DerivativesEngine] (STUB) close_long mkt={market}"
        print(msg)
        return "stub-sig"


# ---------------------------------------------------------------------------
def derivatives_engine_init(cluster: str = "devnet") -> Any:
    """
    Factory used by `main.py`.  Returns either the real engine
    or a stub depending on environment availability.
    """
    if _DRIFT_OK:
        return _RealDerivativesEngine(cluster)
    return _StubDerivativesEngine(cluster)
