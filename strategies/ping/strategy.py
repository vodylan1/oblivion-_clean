"""
PingStrategy – ultra-light heartbeat that sends a 1 lamport transfer bundle
to the Jito Block-Engine every ≈1 s (public-limit safe).

Compatible with:
* solana-py 0.28.x          (pure solana-py, no solders helpers)
* Jito v1 /api/v1/bundles   (JSON-RPC "sendBundle" method)
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import time
from typing import Final

from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.rpc.async_api import AsyncClient
from solana.system_program import SYS_PROGRAM_ID, TransferParams, transfer
from solana.transaction import Transaction

from security.secure_wallet import send_bundle

# ---------------------------------------------------------------------------
# constants / env
# ---------------------------------------------------------------------------

LAMPORTS_PER_SOL: Final[int] = 1_000_000_000

KEYFILE: Final[str] = os.environ.get("OBLIVION_KEYPAIR", "shredstream-keypair.json")
RPC_URL: Final[str] = os.environ.get(
    "SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com"
)

JITO_MIN_INTERVAL: Final[float] = 1.10  # public 1 req / sec limit

# Change to a real recipient later
TIP_ACCOUNT: Final[PublicKey] = PublicKey("11111111111111111111111111111111")

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# signer bootstrap
# ---------------------------------------------------------------------------


def _load_signer(path: str) -> Keypair:
    """Load a solana-cli JSON keypair (64-byte array)"""
    with open(path, "r", encoding="utf-8") as f:
        secret = bytes(json.load(f))
    return Keypair.from_secret_key(secret)


SIGNER: Final[Keypair] = _load_signer(KEYFILE)
SIGNER_PUB: Final[PublicKey] = SIGNER.public_key

log.info("PingStrategy using signer: %s", SIGNER_PUB)


# ---------------------------------------------------------------------------
# strategy
# ---------------------------------------------------------------------------


class Strategy:  # the conductor instantiates this class
    _last_bundle_ts: float = 0.0

    # ------------- conductor entry point ----------------------------------

    async def decide(self, *_a, **_kw) -> None:
        """Wrapper expected by SynergyConductor."""
        try:
            await self._tick_impl()
        except Exception as exc:  # pragma: no cover
            log.warning("[ping] bundle submit failed: %s", exc, exc_info=False)

    # ------------- internal ------------------------------------------------

    async def _tick_impl(self) -> None:
        now = time.time()
        if now - self._last_bundle_ts < JITO_MIN_INTERVAL:
            return  # respect public 1 rps cap

        # 1️⃣  fetch recent blockhash
        async with AsyncClient(RPC_URL) as rpc:
            resp = await rpc.get_latest_blockhash()
            recent_blockhash: str = resp.value.blockhash

        # 2️⃣  build a 0.000001 SOL system-transfer
        ix = transfer(
            TransferParams(
                from_pubkey=SIGNER_PUB,
                to_pubkey=TIP_ACCOUNT,
                lamports=1_000,  # 0.000001 SOL
            )
        )

        tx = Transaction(recent_blockhash=recent_blockhash, fee_payer=SIGNER_PUB)
        tx.add(ix)
        tx.sign(SIGNER)

        # 3️⃣  Jito expects base64-encoded raw bytes
        b64_tx = base64.b64encode(bytes(tx)).decode()
        ref = f"ping-{int(now)}"

        ok = send_bundle([b64_tx], reference=ref, simulate=False)
        if ok:
            log.info("[ping] bundle sent OK – %s", ref)
            self._last_bundle_ts = now
        else:
            log.warning("[ping] bundle submit failed (see above)")
