"""
PingStrategy
============

• Every ~5 s build a tiny 0.000001 SOL tip-transfer and POST it to Jito as a
  single-transaction bundle.

Environment
-----------
OBLIVION_KEYPAIR   path to 64-byte JSON secret key
JITO_BUNDLE_URL    https://mainnet.block-engine.jito.wtf/api/v1/bundles
HELIUS_HTTP        (optional override RPC URL)
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
from solana.system_program import TransferParams, transfer
from solana.transaction import Transaction

# ---------------------------------------------------------------------------

KEYFILE = Path(os.getenv("OBLIVION_KEYPAIR", "shredstream-keypair.json"))
SIGNER: Keypair = Keypair.from_secret_key(bytes(json.load(KEYFILE.open())))
TIP_ACCOUNT = PublicKey("11111111111111111111111111111111")        # TODO real addr

_RPC = AsyncClient(
    os.getenv(
        "HELIUS_HTTP",
        "https://mainnet.helius-rpc.com/?api-key=e702ea0c-f586-4cc6-b2b0-e488fb5358b8",
    )
)

JITO_URL = os.getenv("JITO_BUNDLE_URL", "https://mainnet.block-engine.jito.wtf/api/v1/bundles")

# *** changed ↓↓↓  -- removed http2=True so httpx no longer requires `h2` ***
HTTP = httpx.AsyncClient(base_url=JITO_URL, timeout=10)

# ---------------------------------------------------------------------------


async def _recent_blockhash() -> str:
    resp = await _RPC.get_latest_blockhash()
    return resp.value.blockhash


async def _build_tx() -> str:
    ix = transfer(
        TransferParams(
            from_pubkey=SIGNER.public_key,
            to_pubkey=TIP_ACCOUNT,
            lamports=1_000,  # 0.000001 SOL
        )
    )
    tx = Transaction(recent_blockhash=await _recent_blockhash(), fee_payer=SIGNER.public_key)
    tx.add(ix)
    tx.sign(SIGNER)
    return base64.b64encode(tx.serialize()).decode()


@backoff.on_exception(backoff.expo, httpx.HTTPError, max_tries=5, jitter=None)
async def _send_bundle(b64_tx: str) -> None:
    payload = {"transactions": [b64_tx], "simulation": False}
    r = await HTTP.post("", json=payload)
    if r.status_code not in (200, 202):
        raise httpx.HTTPStatusError(f"Jito status {r.status_code}", request=r.request, response=r)
    print("Jito bundle accepted." if r.status_code == 202 else "Jito bundle executed.")


class Strategy:
    """Minimal heartbeat compatible with SynergyConductor."""

    _last: float = 0.0

    async def decide(self, *_a, **_kw) -> Optional[None]:
        if time.time() - self._last < 1.1:  # Jito public 1 req/s
            return
        try:
            await _send_bundle(await _build_tx())
            self._last = time.time()
        except Exception as exc:
            print("[ping] bundle submit failed:", exc)


def tick(*args, **kw):
    """Sync wrapper for older conductors."""
    return asyncio.run(Strategy().decide(*args, **kw))
