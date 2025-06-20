"""
Minimal wallet helpers + _post_bundle() thin-client for Jito Block-Engine
(using the public JSON-RPC v1 /api/v1/bundles endpoint).

• send_bundle([...], simulate=False)  → raises for non-2xx
• DEFAULT_JITO_URL can be overridden via $JITO_BUNDLE_URL
"""

from __future__ import annotations

import base64
import json
import os
import time
from typing import Iterable, List

import backoff
import httpx
from solana.keypair import Keypair       # solana-py ≤ 0.28
from solana.publickey import PublicKey

__all__ = ["Keypair", "PublicKey", "send_bundle"]

# --------------------------------------------------------------------------- #
#  Configuration
# --------------------------------------------------------------------------- #

DEFAULT_JITO_URL: str = os.getenv(
    "JITO_BUNDLE_URL",
    "https://mainnet.block-engine.jito.wtf/api/v1/bundles",
)
USER_AGENT = "oblivion-ping-strategy/0.1"

# --------------------------------------------------------------------------- #
#  JSON-RPC thin client
# --------------------------------------------------------------------------- #


def _rpc_envelope(b64_txs: List[str], simulate: bool) -> dict:
    """Return a JSON-RPC 2.0 envelope with correct param shape."""
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "sendBundle",
        "params": [
            b64_txs,  # 🡐 param #1 must be an ARRAY of tx strings
            {
                "encoding": "base64",
                "simulation": bool(simulate),
            },
        ],
    }


@backoff.on_exception(
    backoff.expo,
    (httpx.RequestError, httpx.HTTPStatusError),
    max_tries=5,
    jitter=None,
)
def _post_bundle(b64_txs: List[str], simulate: bool = False) -> None:
    """Send the bundle JSON-RPC request. Raises on non-2xx."""
    payload = _rpc_envelope(b64_txs, simulate)

    with httpx.Client(
        headers={"User-Agent": USER_AGENT, "Content-Type": "application/json"},
        timeout=5.0,
    ) as client:
        resp = client.post(DEFAULT_JITO_URL, json=payload)

    if resp.status_code >= 400:
        print("Jito status", resp.status_code, resp.text[:300])
        resp.raise_for_status()


def send_bundle(
    signed_txns: Iterable[str] | str,
    *,
    simulate: bool = False,
) -> None:
    """
    Public wrapper used by strategies. Accepts either a single base-64 string
    or an iterable of them.
    """
    if isinstance(signed_txns, str):
        signed_txns = [signed_txns]
    _post_bundle(list(signed_txns), simulate=simulate)


# --------------------------------------------------------------------------- #
#  Tiny convenience: load a keypair from $OBLIVION_KEYPAIR on import
# --------------------------------------------------------------------------- #

_KEYFILE = os.getenv("OBLIVION_KEYPAIR")
if _KEYFILE and os.path.exists(_KEYFILE):
    with open(_KEYFILE, "r", encoding="utf-8") as f:
        secret_key = json.load(f)  # CLI JSON array -> list[int]
    _SIGNER: Keypair = Keypair.from_secret_key(bytes(secret_key))
else:
    _SIGNER = None  # strategies should handle None gracefully

# re-export for legacy imports
Keypair = Keypair  # noqa: E305 (keeps __all__)
