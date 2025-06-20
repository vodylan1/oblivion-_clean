# strategies/ping/strategy.py  (Solana-py 0.28, solders 0.10.x)

from __future__ import annotations
import os, time, base64, asyncio, logging
from datetime import datetime, timezone

from solana.keypair      import Keypair
from solana.publickey    import PublicKey
from solana.transaction  import Transaction
from solana.system_program import TransferParams, transfer
from solders.rpc.async_api import AsyncClient

from security.secure_wallet import (
    send_bundle,            # -> (status, text)
    load_keypair,           # helper we already wrote
    get_latest_blockhash,   # helper we already wrote
)

_LOG = logging.getLogger(__name__)

# ─── CONFIG ──────────────────────────────────────────────────────────────────
KEYFILE      = os.getenv("OBLIVION_KEYPAIR", "shredstream-keypair.json")
SIGNER: Keypair = load_keypair(KEYFILE)

TIP_ACCOUNT = PublicKey("11111111111111111111111111111111")  # replace later
LAMPORTS     = 1_000              # 0.000001 SOL
TICK_SECONDS = 5                  # one heartbeat every 5 s

_RPC = AsyncClient(os.getenv(
    "HELIUS_HTTP",
    "https://api.mainnet.helius-rpc.com",
))

# ─── STRATEGY CLASS FOR CONDUCTOR ────────────────────────────────────────────
class Strategy:
    name = "ping"

    async def decide(self, *_a, **_kw):
        """SynergyConductor calls this every scheduler tick."""
        now = time.time()
        if now - getattr(self, "_last", 0) < TICK_SECONDS:
            return None          # throttle: too soon

        self._last = now
        await self._send_heartbeat()
        return None              # conductor expects None / bundle-id etc.

    # ─── internals ──────────────────────────────────────────────────────────
    async def _send_heartbeat(self) -> None:
        """Build, sign and post the 1 000 lamport transfer bundle."""
        # 1. fresh blockhash
        bh_resp = await get_latest_blockhash(_RPC)
        recent_bh = bh_resp.value.blockhash

        # 2. transfer instruction
        ix = transfer(
            TransferParams(
                from_pubkey = SIGNER.public_key,
                to_pubkey   = TIP_ACCOUNT,
                lamports    = LAMPORTS,
            )
        )

        # 3. transaction → sign → base64
        tx = Transaction(recent_blockhash = recent_bh, fee_payer = SIGNER.public_key)
        tx.add(ix)
        tx.sign(SIGNER)
        b64_tx = base64.b64encode(tx.serialize()).decode()

        # 4. POST bundle
        status, body = send_bundle([b64_tx])
        if 200 <= status < 300:
            _LOG.info("[ping] ✅ bundle accepted • %s", status)
        else:
            _LOG.warning("[ping] bundle submit failed: %s", body)

# ─── utility so the module can be imported without side-effects ──────────────
__all__ = ["Strategy"]
