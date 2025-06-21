"""
PingStrategy
------------
Sends a 1-lamport transfer every ~5 s so Jito can see liveliness and
priority-fee settings.  Pure *solana-py* (0 .28) – no solders objects.

Environment
-----------
OBLIVION_KEYPAIR   – path to 64-byte JSON array keypair (CLI default)
HELIUS_HTTP        – optional custom RPC; defaults to Helius mainnet
JITO_BUNDLE_URL    – https://mainnet.block-engine.jito.wtf/api/v1/bundles
"""

import asyncio
import base64
import json
import os
from time import time
from typing import List, Optional

import httpx
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from solana.rpc.types import TxOpts
from solana.system_program import TransferParams, transfer
from solana.transaction import Transaction
from solana.message import MessageV0

# ---------------------------------------------------------------------------#
# Config
# ---------------------------------------------------------------------------#
KEYFILE = os.getenv("OBLIVION_KEYPAIR", "shredstream-keypair.json")

HELIUS_HTTP = os.getenv(
    "HELIUS_HTTP",
    "https://rpc.helius.xyz/?api-key=demo",      # fallback public demo key
)

JITO_URL = os.getenv(
    "JITO_BUNDLE_URL",
    "https://mainnet.block-engine.jito.wtf/api/v1/bundles",
)

PING_INTERVAL = 5          # seconds between heart-beats
LAMPORTS       = 1_000     # 0.000001 SOL dummy transfer

# ---------------------------------------------------------------------------#
# Signer
# ---------------------------------------------------------------------------#
with open(KEYFILE, "r", encoding="utf-8") as f:
    secret = bytes(json.load(f))

SIGNER      = Keypair.from_secret_key(secret)
SIGNER_PK   = SIGNER.public_key
TIP_ACCOUNT = PublicKey("11111111111111111111111111111111")   # burn addr

# ---------------------------------------------------------------------------#
# Helpers
# ---------------------------------------------------------------------------#
async def _get_recent_blockhash(rpc: AsyncClient) -> str:
    """Return recent blockhash as base-58 string (solana-py 0.28)."""
    resp = await rpc.get_latest_blockhash()
    return resp.value.blockhash            # already b58 str in 0.28

def _tx_to_b64(tx: Transaction) -> str:
    """Serialize + base64-encode a solana-py Transaction."""
    return base64.b64encode(tx.serialize()).decode()

async def _post_bundle(b64_txs: List[str]) -> httpx.Response:
    """POST bundle to Jito; returns the raw httpx.Response."""
    async with httpx.AsyncClient(timeout=10) as client:
        return await client.post(
            JITO_URL,
            json={
                "transactions": b64_txs,
                "simulation":   False,
            },
        )

# ---------------------------------------------------------------------------#
# Strategy
# ---------------------------------------------------------------------------#
class Strategy:
    def __init__(self) -> None:
        print("[ping] signer:", SIGNER_PK)
        self._rpc  = AsyncClient(HELIUS_HTTP, commitment=Confirmed)
        self._next = 0.0                     # next allowed send epoch

    # ------------------------------------------------------------------- #
    async def tick(self) -> Optional[str]:
        """Heartbeat – builds → signs → bundles → POSTs a 1-lamport tx."""
        now = time()
        if now < self._next:                    # throttle to 1-req/interval
            return None
        self._next = now + PING_INTERVAL

        # 1) latest blockhash
        bh = await _get_recent_blockhash(self._rpc)

        # 2) build transfer
        ix  = transfer(
            TransferParams(
                from_pubkey=SIGNER_PK,
                to_pubkey  =TIP_ACCOUNT,
                lamports   =LAMPORTS,
            )
        )
        # --- Hash **must** be str for MessageV0
        msg = MessageV0.new_with_blockhash([ix], SIGNER_PK, str(bh))  # ← fix
        tx  = Transaction.populate(msg)
        tx.sign(SIGNER)

        # 3) bundle → POST
        r = await _post_bundle([_tx_to_b64(tx)])

        if r.status_code in (200, 202):
            print("[ping] bundle accepted:", r.status_code)
            return r.text

        # ---- failure path ---------------------------------------------
        print("[ping] Jito status", r.status_code)
        try:
            print(r.json())
        except Exception:
            print(r.text)
        return None

    # ------------------------------------------------------------------- #
    # SynergyConductor expects .decide(); just forward to tick()
    # ------------------------------------------------------------------- #
    def decide(self, *args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.create_task(self.tick())
