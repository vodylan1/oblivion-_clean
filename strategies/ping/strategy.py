"""
Heartbeat “ping” strategy:
• every ~5 s builds a 0.000001 SOL tip transfer to a dummy address
• signs with OBLIVION_KEYPAIR
• serialises to base64 and sends via security.secure_wallet.send_bundle
• throttles to ≤ 1 request / second (public BE rate-limit)
"""

from __future__ import annotations

import asyncio
import base64
import logging
import time
from typing import Any

from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.rpc.api import Client
from solana.rpc.types import TxOpts
from solana.transaction import Transaction

from security.secure_wallet import send_bundle, _SIGNER  # re-exported Keypair

log = logging.getLogger(__name__)
RPC = Client("https://api.mainnet-beta.solana.com")
TIP_ACCOUNT = PublicKey("11111111111111111111111111111111")  # dummy


class Strategy:  # loaded by SynergyConductor
    RATE_LIMIT_S = 1.1  # >1 s to stay under 1 req/s

    def __init__(self) -> None:
        if not _SIGNER:
            raise RuntimeError(
                "OBLIVION_KEYPAIR env-var missing or file unreadable"
            )
        self._signer: Keypair = _SIGNER
        self._last_sent = 0.0
        log.info("PingStrategy using signer: %s", self._signer.public_key)

    # -- SynergyConductor will call decide() with *args it ignores -----------
    async def decide(self, *_a: Any, **_kw: Any) -> None:
        await self.tick()

    # ---------------------------------------------------------------------- #
    async def tick(self) -> None:
        now = time.time()
        if now - self._last_sent < self.RATE_LIMIT_S:
            return  # respect 1 req/s

        # 1) fresh blockhash
        bh_resp = RPC.get_latest_blockhash()
        blockhash = bh_resp["result"]["value"]["blockhash"]

        # 2) build 1 000 lamport transfer (0.000001 SOL)
        ix = RPC.request_airdrop(
            self._signer.public_key, 1_000
        )  # simple no-fee dummy; replace with transfer_sol_ix for real

        tx = Transaction(recent_blockhash=blockhash)
        tx.add(ix["result"])
        tx.sign(self._signer)

        # 3) → base64
        b64_tx = base64.b64encode(bytes(tx.serialize())).decode()

        try:
            send_bundle([b64_tx], simulate=False)
            log.info("Ping bundle sent OK (%s)", time.strftime("%H:%M:%S"))
            self._last_sent = now
        except Exception as exc:  # noqa: BLE001
            log.warning("[ping] bundle submit failed: %s", exc)


# optional: alias for earlier conductor versions
Strategy.tick = Strategy.decide  # type: ignore[attr-defined]
