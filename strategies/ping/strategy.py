"""
PingStrategy
============

• Every ~5 s:
    – fetch recent block-hash from Helius RPC
    – build 0.000001 SOL transfer from the bot wallet to TIP_ACCOUNT
    – base-64-encode tx  ➜  POST to Jito bundle endpoint

Assumes:
    $OBLIVION_KEYPAIR      → <path>.json   (64-byte secret-key array)
    $JITO_BUNDLE_URL       → https://mainnet.block-engine.jito.wtf/api/v1/bundles
    $HELIUS_HTTP (optional)
        default:  https://mainnet.helius-rpc.com/?api-key=e702ea0c-f586-4cc6-b2b0-e488fb5358b8
"""

import asyncio
import base64
import json
import os
import time
from pathlib import Path
from typing import Optional

import backoff
import httpx
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.rpc.async_api import AsyncClient
from solana.transaction import Transaction
from solana.system_program import TransferParams, transfer

### ------------------------------------------------------------------------
###  constants & singletons
### ------------------------------------------------------------------------

KEYFILE = Path(os.getenv("OBLIVION_KEYPAIR", "shredstream-keypair.json"))
SIGNER: Keypair = Keypair.from_secret_key(bytes(json.load(KEYFILE.open())))
TIP_ACCOUNT = PublicKey("11111111111111111111111111111111")  # TODO: set real tip addr

_RPC = AsyncClient(
    os.getenv(
        "HELIUS_HTTP",
        "https://mainnet.helius-rpc.com/?api-key=e702ea0c-f586-4cc6-b2b0-e488fb5358b8",
    )
)

JITO_URL = os.getenv("JITO_BUNDLE_URL", "https://mainnet.block-engine.jito.wtf/api/v1/bundles")
HTTP = httpx.AsyncClient(base_url=JITO_URL, http2=True, timeout=10)


### ------------------------------------------------------------------------
###  helpers
### ------------------------------------------------------------------------


async def _recent_blockhash() -> str:
    """Get a fresh block-hash from Helius (string)."""
    resp = await _RPC.get_latest_blockhash()
    return resp.value.blockhash  # str


async def _build_tx() -> str:
    """Return **base-64** encoded transaction."""
    ix = transfer(TransferParams(from_pubkey=SIGNER.public_key, to_pubkey=TIP_ACCOUNT, lamports=1_000))
    tx = Transaction(recent_blockhash=await _recent_blockhash(), fee_payer=SIGNER.public_key)
    tx.add(ix)
    tx.sign(SIGNER)
    return base64.b64encode(tx.serialize()).decode()


@backoff.on_exception(backoff.expo, httpx.HTTPError, max_tries=5, jitter=None)
async def _send_bundle(b64_tx: str) -> None:
    """POST single-tx bundle to Jito. Accepts 200 or 202."""
    payload = {"transactions": [b64_tx], "simulation": False}
    r = await HTTP.post("", json=payload)
    if r.status_code not in (200, 202):
        raise httpx.HTTPStatusError(f"Jito status {r.status_code}", request=r.request, response=r)
    if r.status_code == 202:
        print("Jito bundle accepted (queued).")
    else:
        print("Jito bundle executed immediately.")


### ------------------------------------------------------------------------
###  public Strategy class
### ------------------------------------------------------------------------


class Strategy:
    """Minimal heartbeat strategy compatible with SynergyConductor."""

    _last_sent: float = 0.0

    async def decide(self, *_a, **_kw) -> Optional[None]:
        """Conductor calls this each tick (awaitable)."""
        now = time.time()
        if now - self._last_sent < 1.1:  # Jito public limit ~1 req/s
            return
        try:
            b64_tx = await _build_tx()
            await _send_bundle(b64_tx)
            self._last_sent = now
        except Exception as exc:
            print("[ping] bundle submit failed:", exc)


### ------------------------------------------------------------------------
###  module-level (sync) tick alias for earlier conductor versions
### ------------------------------------------------------------------------

def tick(*args, **kw):
    """Backward-compat wrapper if conductor still expects sync tick()."""
    return asyncio.run(Strategy().decide(*args, **kw))
