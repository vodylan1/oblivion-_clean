"""
security/secure_wallet.py
--------------------------------------------------------------------
Utilities for building / signing Solana transactions **and**
submitting bundles to Jito Block-Engine (v1 `POST /api/v1/bundles`).

• build_tip_transfer() → str(base-64)        – tiny 0.000001 SOL tip tx
• send_bundle([b64_tx], simulate=False) → dict(JSON-RPC result or error)
"""

from __future__ import annotations

import base64
import json
import os
import time
from typing import List

import backoff
import httpx
from solana.keypair import Keypair          # ← re-export for legacy imports

from solana.rpc.api import Client
from solana.rpc.types import TxOpts
from solana.transaction import Transaction
from solana.system_program import TransferParams, transfer

# ---------------------------------------------------------------------------
#  Environment
# ---------------------------------------------------------------------------

JITO_BUNDLES_URL: str = os.getenv(
    "JITO_BUNDLE_URL",
    "https://mainnet.block-engine.jito.wtf/api/v1/bundles",
)
RPC_HTTP: str = os.getenv(
    "HELIUS_HTTP",
    "https://api.mainnet.helius-rpc.com",
)

SIGNER_KEYPAIR = Keypair.from_secret_key(
    bytes(json.load(open(os.getenv("OBLIVION_KEYPAIR", "shredstream-keypair.json"))))
)
SIGNER_PUBKEY = SIGNER_KEYPAIR.public_key

_RPC = Client(RPC_HTTP)

# ---------------------------------------------------------------------------
#  Helpers
# ---------------------------------------------------------------------------


def _latest_blockhash() -> str:
    """Return the recent blockhash (str) for tx signing."""
    resp = _RPC.get_latest_blockhash()
    return resp["result"]["value"]["blockhash"]


def build_tip_transfer(lamports: int = 1_000) -> str:
    """
    Build a **signed** System-Program transfer (tip) tx and
    return it as a base-64 string suitable for Jito.
    """
    ix = transfer(
        TransferParams(
            from_pubkey=SIGNER_PUBKEY,
            to_pubkey=SIGNER_PUBKEY,               # self-transfer “tip”
            lamports=lamports,
        )
    )
    tx = Transaction().add(ix)
    tx.recent_blockhash = _latest_blockhash()
    tx.sign(SIGNER_KEYPAIR)

    return base64.b64encode(tx.serialize()).decode()


# ---------------------------------------------------------------------------
#  Bundle submission
# ---------------------------------------------------------------------------


def _jito_client() -> httpx.Client:
    """Shared sync HTTP client – 10 s total timeout."""
    return httpx.Client(timeout=10.0, headers={"Content-Type": "application/json"})


@backoff.on_exception(backoff.expo, httpx.HTTPError, max_tries=5)
def _post_bundle(body: dict) -> dict:
    """Low-level POST wrapper with back-off."""
    with _jito_client() as client:
        r = client.post(JITO_BUNDLES_URL, json=body)
        if r.status_code != 200_
