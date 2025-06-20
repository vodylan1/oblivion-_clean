"""
Secure wallet & Jito bundle helper
• loads a Keypair from JSON-array file (path in $OBLIVION_KEYPAIR)
• signs and base64-encodes a Transaction
• POSTs the bundle to Jito’s public REST endpoint with robust back-off
"""

from __future__ import annotations

import base64
import json
import os
import time
from typing import List

import backoff
import httpx
from solana.keypair import Keypair  # solana-py 0.28
from solana.transaction import Transaction

# ---------------------------------------------------------------------------#
#  Configuration
# ---------------------------------------------------------------------------#

# Path to JSON array keypair (created with `solana-keygen new -o my.json`)
KEY_PATH = os.getenv("OBLIVION_KEYPAIR", "shredstream-keypair.json")

# Jito public block-engine bundle endpoint
JITO_BUNDLE_URL = os.getenv(
    "JITO_BUNDLE_URL",
    "https://mainnet.block-engine.jito.wtf/api/v1/bundles",
)

# ----------------------------------------------------------------------------
#  Wallet helpers
# ----------------------------------------------------------------------------
def _load_keypair(path: str = KEY_PATH) -> Keypair:
    with open(path, "r", encoding="utf-8") as f:
        secret = bytes(json.load(f))
    return Keypair.from_secret_key(secret)

SIGNER: Keypair = _load_keypair()

# ----------------------------------------------------------------------------
#  Bundle sender
# ----------------------------------------------------------------------------
def _jito_post(payload: dict) -> httpx.Response:
    return httpx.post(
        JITO_BUNDLE_URL,
        json=payload,
        timeout=10.0,
    )

@backoff.on_exception(
    backoff.expo, httpx.HTTPStatusError,
    max_tries=5,
    giveup=lambda e: e.response.status_code == 400,  # schema / wallet errors – don’t retry
    jitter=None,
)
def _safe_send(payload: dict) -> httpx.Response:
    resp = _jito_post(payload)
    if resp.status_code == 429:                        # global 1 rps limit
        raise httpx.HTTPStatusError("429", request=resp.request, response=resp)
    if resp.status_code >= 400:
        print("Jito status", resp.status_code, resp.text)
        resp.raise_for_status()
    return resp

# public helper used by strategies
def send_bundle(tx_list: List[str], simulate: bool = False) -> None:
    """
    Push a list of base-64 encoded txs to Jito.
    Jito v1 schema: {'transactions': [...], 'simulation': bool}
    """
    if not tx_list:                     # nothing to send
        return
    payload = {
        "transactions": tx_list,
        "simulation": simulate,
    }
    _safe_send(payload)

# ----------------------------------------------------------------------------
#  Convenience wrapper for a single Transaction instance
# ----------------------------------------------------------------------------
def sign_and_send(tx: Transaction, simulate: bool = False) -> None:
    tx.recent_blockhash = str(tx.recent_blockhash)  # ensure str for solana-py
    tx.sign(SIGNER)
    b64_tx = base64.b64encode(tx.serialize()).decode()
    send_bundle([b64_tx], simulate=simulate)
