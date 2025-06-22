"""
Heartbeat “Ping” strategy
─────────────────────────
Every *period* seconds:
  • fetch latest block‑hash
  • create a 1 000‑lamport System Transfer to OBLIVION_PING_TIP
  • wrap it in a VersionedTransaction v0
  • post as a single‑tx bundle to Jito
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Final, List

from solders.hash import Hash
from solders.instruction import Instruction as SoldersIx
from solders.message import MessageV0
from solders.pubkey import Pubkey
from solders.system_program import transfer, TransferParams
from solders.transaction import VersionedTransaction
from solana.rpc.async_api import AsyncClient

from security.secure_wallet import SIGNER, send_bundle

_LOG = logging.getLogger(__name__)
_RPC_URL: Final[str] = "https://api.mainnet-beta.solana.com"
_TIP_ACCT: Final[Pubkey] = Pubkey.from_string(
    os.getenv("OBLIVION_PING_TIP", "11111111111111111111111111111111")
)
_LAMPORTS: Final[int] = 1_000


class Strategy:  # class name expected by loader
    def __init__(self, period: int = 5):
        self._period = period
        self._task: asyncio.Task | None = None

    # SynergyConductor calls this once per tick
    async def decide(self, *_):  # accept *args for forward‑compat
        if self._task is None:
            self._task = asyncio.create_task(self._loop())

    # ────────────────── internal worker ──────────────────
    async def _loop(self):
        _LOG.info("PingStrategy signer: %s", SIGNER.pubkey())
        rpc = AsyncClient(_RPC_URL, commitment="processed")

        while True:
            try:
                # 1) latest block‑hash
                bh = Hash.from_string(
                    (await rpc.get_latest_blockhash()).value.blockhash
                )

                # 2) system‑transfer instruction
                ix: SoldersIx = transfer(
                    TransferParams(
                        from_pubkey=SIGNER.pubkey(),
                        to_pubkey=_TIP_ACCT,
                        lamports=_LAMPORTS,
                    )
                )

                # 3) message v0 + tx
                msg = MessageV0.new(SIGNER.pubkey(), [ix], [], bh)
                tx = VersionedTransaction(msg, [SIGNER])

                # 4) send
                bundle_id = await send_bundle([tx])
                _LOG.info("Ping bundle sent • id=%s", bundle_id)
            except Exception as exc:
                _LOG.warning("Ping failed: %s", exc, exc_info=False)

            await asyncio.sleep(self._period)
