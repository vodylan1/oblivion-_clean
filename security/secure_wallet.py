"""
Secure wallet helpers:
* Keypair loading (JSON array file expected)
* send_bundle()  – posts a signed bundle to Jito Block-Engine via JSON-RPC
"""

from __future__ import annotations

import base64, json, os, time, typing as _t

import backoff
import httpx
from solders.keypair    import Keypair                   # new vector types
from solders.pubkey     import Pubkey
from solders.signature  import Signature
from solders.transaction import VersionedTransaction

# --------------------------------------------------------------------------- #
#  Configuration
# --------------------------------------------------------------------------- #

# Jito v1 JSON-RPC endpoint (override via env-var)
JITO_RPC_URL: str = os.environ.get(
    "JITO_BUNDLE_URL",
    "https://mainnet.block-engine.jito.wtf/api/v1/rpc",
)

# path to 64-byte JSON array keypair file
KEYFILE: str = os.getenv("OBLIVION_KEYPAIR", "shredstream-keypair.json")

# --------------------------------------------------------------------------- #
#  Keypair loader
# --------------------------------------------------------------------------- #

def _load_signer() -> Keypair:
    with open(KEYFILE, "r", encoding="utf-8") as f:
        secret = bytes(json.load(f))          # 64-byte JSON array
    return Keypair.from_bytes(secret)

SIGNER: Keypair = _load_signer()
SIGNER_PUB: Pubkey = SIGNER.pubkey()

# --------------------------------------------------------------------------- #
#  Bundle sender – JSON-RPC sendBundle
# --------------------------------------------------------------------------- #

_jsonrpc_id: int = 1  # monotonic id

def _json_rpc(method: str, params: list[object]) -> dict[str, _t.Any]:
    global _jsonrpc_id
    _jsonrpc_id += 1
    return {"jsonrpc": "2.0", "method": method, "params": params, "id": _jsonrpc_id}


@backoff.on_exception(backoff.expo, httpx.HTTPStatusError, max_tries=5, jitter=backoff.full_jitter)
def _post_bundle(json_body: dict[str, _t.Any]) -> dict[str, _t.Any]:
    """POST the bundle, raise on non-200, return parsed json."""
    with httpx.Client(timeout=15.0) as client:
        resp = client.post(JITO_RPC_URL, json=json_body)
        if resp.status_code >= 400:
            # Print once for visibility
            print(f"Jito status {resp.status_code}", resp.text)
            resp.raise_for_status()
        return resp.json()


def send_bundle(
    b64_txs: list[str],
    simulate: bool = False,
    reference: str | None = None,
) -> dict[str, _t.Any]:
    """
    Submit a bundle (list of base64 txs) to Jito Block-Engine.

    Returns the JSON-RPC response dict or raises httpx.HTTPStatusError.
    """
    params: dict[str, _t.Any] = {
        "transactions": b64_txs,
        "simulation":   simulate,
    }
    if reference:
        params["reference"] = reference

    payload = _json_rpc("sendBundle", [params])  # params must be an array!

    return _post_bundle(payload)


# --------------------------------------------------------------------------- #
#  Convenience – build & send single tx
# --------------------------------------------------------------------------- #

def sign_and_send(tx: VersionedTransaction, reference: str | None = None) -> dict[str, _t.Any]:
    b64_tx = base64.b64encode(bytes(tx)).decode()
    return send_bundle([b64_tx], reference=reference)
