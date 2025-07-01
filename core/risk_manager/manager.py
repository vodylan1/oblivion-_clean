"""Central risk-sizing + guardrails façade."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Final

from config.parameters import VAR_CAP_RATIO
from risk_policies import load_policy
from security.secure_wallet import get_wallet_balance_usd
from trade_types import TradeSignal  # ← whatever your project calls this

# ---------------------------------------------------------------------------


@dataclass(slots=True)
class _RuntimeCaps:
    bucket_cap: float = 0.0  # USD limit per token bucket

    def refresh(self) -> None:
        """Recompute caps from live wallet balance + policy."""
        bal_usd = get_wallet_balance_usd()
        policy = load_policy()  # default static_25 unless overridden
        self.bucket_cap = policy.position_limit_usd(bal_usd)


class RiskManager:
    """Singleton providing risk checks & position sizing."""

    _INSTANCE: "RiskManager | None" = None
    _caps: _RuntimeCaps

    # tuneable var-margin cap (global)
    _var_cap_ratio: Final[float] = VAR_CAP_RATIO

    # --------------------------------------------------------------------- #
    #  life-cycle helpers
    # --------------------------------------------------------------------- #

    def __init__(self) -> None:
        self._caps = _RuntimeCaps()
        self._caps.refresh()

    @classmethod
    def instance(cls) -> "RiskManager":
        if cls._INSTANCE is None:
            cls._INSTANCE = cls()
        return cls._INSTANCE

    # --------------------------------------------------------------------- #
    #  public API
    # --------------------------------------------------------------------- #

    @property
    def bucket_cap(self) -> float:
        """USD cap per token bucket."""
        return self._caps.bucket_cap

    # ------------------------------------------------------------------ #

    def pre_trade(self, signal: TradeSignal, notional_usd: float) -> bool:
        """
        True if the proposed `notional_usd` passes risk checks.

        Current checks:
        • bucket-cap (per-token)
        • VAR-cap (global equity %)  — stubbed for now
        """
        if notional_usd > self.bucket_cap:
            return False
        # TODO: plug in VAR check once equity curves wired-up
        return True
