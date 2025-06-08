# pipelines/execution_engine.py
"""
Execution-Engine (Phase-8/9 stub)

* position-sizing based on wallet balance + RISK_PCT
* BUY / SELL stubs (mock-mode or real-mode later)
* exposes a minimal public surface so that
  - unit-tests run (RISK_PCT, _size_lamports)
  - main.py can still import `execution_engine_init`

This file will be upgraded in later PRs when real TX submission,
Jupiter routing and PnL accounting land.
"""

from __future__ import annotations

import json
import pathlib
import time
from typing import Final

# ──────────────────────────────────────────────────────────────────────────
# Constants & config
# ──────────────────────────────────────────────────────────────────────────

_ROOT = pathlib.Path(__file__).resolve().parents[1]
_PARAMS_F = _ROOT / "config" / "parameters.json"

with _PARAMS_F.open("r", encoding="utf-8") as fh:
    _PARAMS: dict = json.load(fh)

#: % of wallet balance to risk per position (exposed for unit-tests)
RISK_PCT: Final[float] = float(_PARAMS.get("risk_pct", 0.02))

#: default execution environment (“mock”, “real_mainnet” …)
_ENV: str = "mock"

# __all__ tells `from … import *` what to expose
__all__ = [
    "RISK_PCT",
    "execute_trade",
    "execution_engine_init",  # legacy shim
    "_position_size_lamports",
    "_size_lamports",         # legacy shim for tests
]

# ──────────────────────────────────────────────────────────────────────────
# Balance helpers
# ──────────────────────────────────────────────────────────────────────────


def _balance_lamports(cluster: str) -> int:
    """
    Return current SOL balance in **lamports** for the active wallet.

    In *mock* mode we just fake `10 SOL` to keep maths deterministic.
    """
    if cluster == "mock":
        return int(10 * 1e9)  # 10 SOL
    # TODO: real RPC call once secure_wallet & RPC are wired.
    return int(0 * 1e9)


# ──────────────────────────────────────────────────────────────────────────
# Position sizing
# ──────────────────────────────────────────────────────────────────────────


def _position_size_lamports(*, price_usd: float) -> int:
    """
    How many lamports should we risk on the next BUY?

    Args
    ----
    price_usd : float
        Current SOL-USD price (only needed when we later risk a % of USD
        account value; for now we risk lamports directly so this param
        isn’t used but kept for future-proofing).

    Returns
    -------
    int
        Lamports we are willing to deploy.
    """
    bal = _balance_lamports(_ENV)
    lamports_to_risk = int(bal * RISK_PCT)
    return max(lamports_to_risk, 1_000)  # never return 0


# ──────────────────────────────────────────────────────────────────────────
# Trade dispatcher
# ──────────────────────────────────────────────────────────────────────────


def execute_trade(decision: str, price: float | None) -> None:
    """
    Public entry-point used by `main.py`.

    Parameters
    ----------
    decision : {"BUY", "SELL", "HOLD"}
    price    : float | None
        Latest SOL price (may be *None* if feed failed).
    """
    if decision == "BUY":
        _handle_buy(price)
    elif decision == "SELL":
        _handle_sell(price)
    else:  # HOLD / unknown
        return


def _handle_buy(price: float | None) -> None:
    """Simulated / placeholder BUY."""
    lamports = _position_size_lamports(price_usd=price or 0)
    if _ENV == "mock":
        print(
            f"[ExecutionEngine] (MOCK) BUY {lamports/1e9:.4f} SOL "
            f"at ${price:.2f} – risk {RISK_PCT*100:.1f}%"
        )
    else:
        # TODO: real Jupiter swap once wired.
        print(
            f"[ExecutionEngine] LIVE-MODE BUY {lamports/1e9:.4f} SOL "
            f"at ${price:.2f} – tx submitted (stub)"
        )


def _handle_sell(price: float | None) -> None:
    """Simulated / placeholder SELL."""
    if _ENV == "mock":
        print(f"[ExecutionEngine] (MOCK) SELL – price ${price:.2f}")
    else:
        print(f"[ExecutionEngine] LIVE-MODE SELL – price ${price:.2f} (stub)")


# ──────────────────────────────────────────────────────────────────────────
# Compatibility shims (legacy tests / old imports)
# ──────────────────────────────────────────────────────────────────────────


def _size_lamports(_: str | None = None) -> int:  # noqa: N802
    """
    **Legacy helper** kept so `tests/test_position_sizing.py` passes.

    Signature kept identical to old version; the `cluster` arg is ignored.
    """
    return _position_size_lamports(price_usd=1.0)


def execution_engine_init(env: str) -> None:  # noqa: N802
    """
    **Legacy initializer** so `main.py` can still import it.

    In the new architecture, module import performs initialisation, so
    this function just sets the global mode string and prints a banner.
    """
    global _ENV
    _ENV = "mock" if env == "mock" else "real_mainnet"
    print(f"[ExecutionEngine] Initialised – mode = {_ENV}")


# ──────────────────────────────────────────────────────────────────────────
# Quick manual test
# ──────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    execution_engine_init("mock")
    for _ in range(3):
        execute_trade("BUY", price=150.0 + _)
        time.sleep(0.5)
