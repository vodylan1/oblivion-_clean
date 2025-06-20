"""
Heartbeat strategy:
• every ≈1 s creates a 0.000001 SOL SystemProgram::Transfer
• signs with SIGNER and ships it via security.secure_wallet.sign_and_send
"""

from __future__ import annotations

import logging
import time
from typing import Any

from solana.publickey import PublicKey
from solana.rpc.async_api import AsyncClient
from solana.transaction import Transaction
from solders.system_program import TransferParams, transfer

from security.secure_wallet import SIGNER, sign_and_send

log = logging.getLogger(__name__)

LAMPORTS_PER_SOL = 1_000_000_000
TIP_ACCOUNT = PublicKey("11111111111111111111111111111111")   # <- replace later

# single global RPC client (Helius key comes from env)
_RPC = AsyncClient(os.getenv("HELIUS_HTTP", "https://api.mainnet.helius-rpc.com"))

class Strategy:
    """Synergy-Conductor expects each strategy to expose `decide(clock)`."""

    def __init__(self) -> None:
        self._last_send: float = 0.0
        log.info("PingStrategy using signer: %s", SIGNER.public_key)

    # conductor passes `(clock,)`; we ignore it
    async def decide(self, *_: Any, **__: Any) -> None:
        now = time.time()
        if now - self._last_send < 1.1:      # hard 1 rps
            return
        self._last_send = now

        # 1) latest blockhash
        bh_resp = await _RPC.get_latest_blockhash()
        blockhash = bh_resp.value.blockhash

        # 2) build SystemProgram transfer (1_000 lamports = 0.000001 SOL)
        params = TransferParams(
            from_pubkey=PublicKey(str(SIGNER.public_key)),
            to_pubkey=TIP_ACCOUNT,
            lamports=1_000,
        )
        ix = transfer(params)

        # 3) sign & send via helper
        tx = Transaction(recent_blockhash=blockhash, fee_payer=SIGNER.public_key)
        tx.add(ix)
        try:
            sign_and_send(tx, simulate=False)
            log.info("ping tick ➜ %s", time.strftime("%H:%M:%S"))
        except Exception as exc:  # noqa: BLE001
            log.warning("[ping] bundle submit failed: %s", exc)
