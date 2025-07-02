"""Pipeline-level proxy to the real secure_wallet helpers."""

from security.secure_wallet import get_wallet_balance_usd

__all__ = ["get_wallet_balance_usd"]
