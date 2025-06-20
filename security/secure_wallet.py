"""
Helpers for signing and submitting bundles to Jito Block-Engine
(works with solana-py 0.28 and solders 0.10).

Functions
---------
load_keypair(path)  -> Keypair
send_bundle(txs_b64: list[str], simulate=False) -> bool
"""

from __future__ import annotations

import base64
import json
import logging
import os
import time
from pathlib import Path
from typing import List

import backoff
import httpx
from solana.keypair import Keypair  # re-exported for pipelines.jito_submit
from solana.rpc.api import Client

# --------------------------------------------------------------------------- #
# configuration
# --------------------------------------------------------------------------- #

_LOG = logging.getLogger(__name__)

JITO_URL: str = os.getenv(
    "JITO_BUNDLE_URL",
    "https://mainnet.block-engine.jito.wtf/api/v1/bundles",
)

# Public Helius endpoint if the user did not override
_RPC = Client(os.getenv("HELIUS_HTTP", "https://api.mainnet.helius-rpc.com"))

# --------------------------------------------------------------------------- #
# key management
# --------------------------------------------------------------------------- #


def load_keypair(path: str | os.PathLike) -> Keypair:
    """
    Load a Solana CLI–format keypair (JSON array of 64 numbers).

    Parameters
    ----------
    path : str or Path
        Path to e.g. ``shredstream-keypair.json``

    Returns
    -------
    Keypair
    """
    path = Path(path).expanduser().resolve()
    secret = bytes(json.loads(path.read_text()))
    return Keypair.from_secret_key(secret)


# --------------------------------------------------------------------------- #
# bundle submission
# --------------------------------------------------------------------------- #


def _body(txs_b64: List[str], simulate: bool) -> dict:
    return {
        "transactions": txs_b64,  # <-- Jito v1 key
        "simulation": simulate,
    }


# Retry on 429 (“Network congested. Endpoint is globally rate limited.”)
@backoff.on_exception(
    backoff.expo,
    httpx.HTTPStatusError,
    max_tries=5,
    giveup=lambda e: e.response.status_code in (400, 404),
)
def _post_bundle(body: dict) -> httpx.Response:
    r = httpx.post(JITO_URL, json=body, timeout=5.0)
    status = r.status_code
    if status not in (200, 202):
        # log the raw body for fast debugging (e.g. {"error":"unknown wallet"} )
        _LOG.warning("Jito status %s %s", status, r.text)
        r.raise_for_status()  # ⇢ retry or bubble
    else:
        _LOG.info("Jito bundle accepted (%s)", status)
    return r


def send_bundle(txs_b64: List[str], simulate: bool = False) -> bool:
    """
    Submit one or more **base-64** encoded transactions to Jito.

    Returns True when HTTP layer returned 200 **or** 202.
    Raises httpx.HTTPStatusError otherwise (already back-off wrapped).
    """
    body = _body(txs_b64, simulate)
    _post_bundle(body)
    return True


# --------------------------------------------------------------------------- #
# convenience – fetch recent blockhash (8 × per second public limit)
# --------------------------------------------------------------------------- #


def get_latest_blockhash() -> str:
    """Return a recent blockhash as **base-58 string** (for solana-py Tx)."""
    resp = _RPC.get_latest_blockhash()
    # solana-py 0.28: resp["result"]["value"]["blockhash"]
    return resp["result"]["value"]["blockhash"]


# --------------------------------------------------------------------------- #
# re-export for legacy imports
# --------------------------------------------------------------------------- #

__all__ = ["Keypair", "load_keypair", "send_bundle", "get_latest_blockhash"]
