from typing import TypedDict, Dict, Any


class WalletProfile(TypedDict):
    label: str          # e.g. 'whale', 'dev', 'bot'
    pnl: float          # historical PnL
    tx_count: int


class WalletProfiler:
    """Caches labelled wallets & updates basic stats."""

    def __init__(self) -> None:
        self._cache: Dict[str, WalletProfile] = {}

    def update(self, wallet: str, delta_pnl: float) -> None:
        profile = self._cache.setdefault(wallet, {"label": "unknown", "pnl": 0.0, "tx_count": 0})
        profile["pnl"] += delta_pnl
        profile["tx_count"] += 1

    def label(self, wallet: str) -> str:
        return self._cache.get(wallet, {}).get("label", "unknown")
