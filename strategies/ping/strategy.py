"""
PingStrategy
------------
Sends a 1 lamport transfer every ~5 s so Jito can see liveliness and
priority-fee settings.  Pure *solana-py* (0.28) – no solders objects.

Environment
-----------
OBLIVION_KEYPAIR   – path to 64-byte JSON array keypair (CLI default)
HELIUS_HTTP        – optional custom RPC; defaults to mainnet
JITO_BUNDLE_URL    – https://mainnet.block-engine.jito.wtf/api/v1/bundles
"""

import base64
import asyncio
import json
import os
from time import time
from typing import Optional, List

import httpx
from solana.keypair               import Keypair
from solana.publickey             import PublicKey
from solana.rpc.async_api         import AsyncClient
from solana.rpc.commitment        import Confirmed
from solana.transaction           import Transaction
from solana.system_program        import TransferParams, transfer
from solana.rpc.types             import TxOpts

# ------------------------------------------------------------------ #
#  Config
# ------------------------------------------------------------------ #
KEYFILE        = os.getenv("OBLIVION_KEYPAIR", "shredstream-keypair.json")
HELIUS_HTTP    = os.getenv("HELIUS_HTTP",
                           "https://rpc.helius.xyz/?api-key=demo")
JITO_URL       = os.getenv("JITO_BUNDLE_URL",
                           "https://mainnet.block-engine.jito.wtf/api/v1/bundles")
PING_INTERVAL  = 5         # seconds
LAMPORTS       = 1_000     # 0.000001 SOL tip

# ------------------------------------------------------------------ #
#  Load signer
# ------------------------------------------------------------------ #
with open(KEYFILE, "r", encoding="utf-8") as f:
    secret = bytes(json.load(f))
SIGNER      = Keypair.from_secret_key(secret)
SIGNER_PK   = SIGNER.public_key
TIP_ACCOUNT = PublicKey("11111111111111111111111111111111")   # burn addr

# ------------------------------------------------------------------ #
#  Helpers
# ------------------------------------------------------------------ #
async def _fetch_blockhash(rpc: AsyncClient) -> str:
    """Return recent blockhash as base-58 string."""
    resp = await rpc.get_latest_blockhash()
    return resp.value.blockhash

def _tx_to_b64(tx: Transaction) -> str:
    return base64.b64encode(tx.serialize()).decode()

async def _post_bundle(b64_txs: List[str]) -> httpx.Response:
    """Send bundle to Jito; 200 OK or 202 Accepted is success."""
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(
            JITO_URL,
            json={"transactions": b64_txs, "simulation": False},
        )
    return r

# ------------------------------------------------------------------ #
#  Strategy
# ------------------------------------------------------------------ #
class Strategy:
    def __init__(self) -> None:
        print("[ping] signer:", SIGNER_PK)

        self._rpc   = AsyncClient(HELIUS_HTTP, commitment=Confirmed)
        self._next  = 0.0                 # next permitted send epoch

    # ---------------------------------------------- #
    async def tick(self) -> Optional[str]:
        """Runs every scheduler cycle; returns str on success, else None."""
        now = time()
        if now < self._next:                       # 1 req / PING_INTERVAL
            return None
        self._next = now + PING_INTERVAL

        # 1) Fetch recent blockhash
        recent_hash = await _fetch_blockhash(self._rpc)

        # 2) Build transfer 1 lamport → burn addr
        ix = transfer(
            TransferParams(
                from_pubkey=SIGNER_PK,
                to_pubkey=TIP_ACCOUNT,
                lamports=LAMPORTS,
            )
        )
        tx = Transaction(recent_blockhash=recent_hash, fee_payer=SIGNER_PK)
        tx.add(ix)
        tx.sign(SIGNER)

        # 3) Encode & send bundle
        b64_tx = _tx_to_b64(tx)
        resp = await _post_bundle([b64_tx])

        if resp.status_code in (200, 202):
            print("[ping] bundle accepted:", resp.status_code)
            return resp.text      # or some success marker

        # --- failure path ------------------------------------------------
        print("[ping] Jito status", resp.status_code)
        try:
            print(resp.json())
        except Exception:
            print(resp.text)
        return None

    # ------------------------------------------------------------------ #
    #  Compatibility shim – SynergyConductor expects .decide()
    # ------------------------------------------------------------------ #
    def decide(self, *args, **kwargs):
        """Alias for tick(); required by SynergyConductor."""
        # If the conductor happens to call decide() synchronously,
        # schedule tick() in the current loop.
        loop = asyncio.get_event_loop()
        return loop.create_task(self.tick())
