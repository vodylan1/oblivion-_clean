"""
exec_mesh.py
Phase 10.2 – now capital‑aware for notional sizing
"""

import os
import random
from solana.transaction import Transaction

from notifications.discord_notifier import notify_discord
from security.secure_wallet import sign_and_send
from core.risk_manager.manager import RiskManager

_risk_mgr = RiskManager()   # singleton for pipes

# pull from secrets or env
def _get_helius_url() -> str:
    return os.getenv("HELIUS_STAKED_URL", "https://mainnet.helius-rpc.com?api-key=YOUR_KEY")


async def send_swap_transaction(route_str: str, notional_usd: float, tip_cu: int) -> None:
    """
    Builds dummy TX, enforces size cap via RiskManager.
    """
    cap = _risk_mgr.position_limit_usd()
    notional_usd = min(notional_usd, cap)

    tx = Transaction()   # TODO real IX build

    use_helius = (random.random() < 0.85)
    rpc_url = _get_helius_url() if use_helius else "https://api.mainnet-beta.solana.com"

    sig = await sign_and_send(tx, rpc_url)
    msg = (f"[exec_mesh] SWAP route={route_str}, notional=${notional_usd:,.0f}, "
           f"tip={tip_cu}, sig={sig}")
    print(msg)
    await notify_discord(msg)
