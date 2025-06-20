"""
Heartbeat strategy – every ~5 s it builds a 0.000001 SOL transfer
(from the bot wallet to TIP_ACCOUNT) and sends it as a single-tx bundle.

Requirements
------------
* solana-py 0.28
* security.secure_wallet with send_bundle() accepting 200 / 202
"""

from __future__ import annotations

import base64
import asyncio
import logging
import os
import time
from datetime import datetime, timezone

from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.transaction import Transaction
from solana.system_program import TransferParams, transfer

from security.secure_wallet import (
    send_bundle,
    load_keypair,
    get_latest_blockhash,
)

_LOG = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# constants / config
# --------------------------------------------------------------------------- #

KEYFILE = os.getenv("OBLIVION_KEYPAIR", "shredstream-keypair.json")
SIGNER: Keypair = load_keypair(KEYFILE)

TIP_ACCOUNT = PublicKey.from_string(
    "11111111111111111111111111111111"
)  # TODO: put real tip wallet here

LAMPORTS = 1_000  # 0.000001 SOL

TICK_SECONDS = 5
_last_sent = 0.0  # global throttle

# --------------------------------------------------------------------------- #
# strategy class expected by SynergyConductor
# --------------------------------------------------------------------------- #


class Strategy:
    name = "ping"

    # ---------- SynergyConductor calls this every scheduler tick ----------
    async def decide(self, *_a, **_kw):
        global _last_sent

        now = time.time()
        if now - _last_sent < TICK_SECONDS:
            return None  # throttle

        _last_sent = now
        await _send_heartbeat()
        return None  # conductor expects None / bundle-id / etc.


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #


async def _send_heartbeat() -> None:
    """Build + sign a tiny transfer and post it to Jito."""
    # 1) instruction
    ix = transfer(
        TransferParams(
            from_pubkey=SIGNER.public_key,
            to_pubkey=TIP_ACCOUNT,
            lamports=LAMPORTS,
        )
    )

    # 2) fresh blockhash
    recent = get_latest_blockhash()

    # 3) transaction
    tx = Transaction(recent_blockhash=recent, fee_payer=SIGNER.public_key)
    tx.add(ix)
    tx.sign(SIGNER)

    # 4) serialize → base64
    b64_tx = base64.b64encode(tx.serialize()).decode()

    # 5) POST bundle (no simulation flag here – live net)
    try:
        send_bundle([b64_tx])
        _LOG.info("ping tick ➜ %s", datetime.now(timezone.utc).isoformat(timespec="seconds"))
    except Exception as exc:
        _LOG.warning("[ping] bundle submit failed: %s", exc)
