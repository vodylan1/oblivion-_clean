"""
exec_mesh.py
Phase 10.1 – real TX sending, partial example with Helius staked + fallback
"""

import os
import random
from solana.transaction import Transaction

from notifications.discord_notifier import notify_discord
from security.secure_wallet import sign_and_send

# pull from secrets or env
def _get_helius_url() -> str:
    # assume from env or secrets
    return os.getenv("HELIUS_STAKED_URL", "https://mainnet.helius-rpc.com?api-key=YOUR_KEY")

async def send_swap_transaction(route_str: str, notional: float, tip_cu: int) -> None:
    """
    Replaces the stub with a real sign+send approach:
      1) build a minimal dummy transaction
      2) sign with secure_wallet
      3) post to Helius or fallback
    """
    # building a dummy transaction or a real aggregator IX is more complex.
    # We'll just sign a blank tx for demonstration:
    tx = Transaction()

    # random 85% chance we do Helius, else fallback
    use_helius = (random.random()<0.85)
    rpc_url = _get_helius_url() if use_helius else "https://api.mainnet-beta.solana.com"

    sig = await sign_and_send(tx, rpc_url)
    msg = f"[exec_mesh] SWAP TX => route={route_str}, notional={notional}, tip={tip_cu}, sig={sig}"
    print(msg)
    await notify_discord(msg)

async def send_snipe_transaction(token_mint: str, notional: float, max_slip: float, tip_cu: int) -> None:
    """
    Real sign+send for meme snipe. This is still a demo, building a blank TX.
    """
    tx = Transaction()
    # in reality, you'd build the instructions to add liquidity or buy tokenMint
    # with e.g. USDC from aggregator route. This is a large topic itself.

    use_helius = (random.random()<0.85)
    rpc_url = _get_helius_url() if use_helius else "https://api.mainnet-beta.solana.com"

    sig = await sign_and_send(tx, rpc_url)
    msg = f"[exec_mesh] SNIPETX => mint={token_mint}, notional={notional}, slip={max_slip}, tip={tip_cu}, sig={sig}"
    print(msg)
    await notify_discord(msg)
