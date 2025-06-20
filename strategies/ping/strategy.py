"""
PingStrategy – tiny heartbeat that tips a dust amount of SOL every N seconds.

Compatible with **solana-py 0.28.x**  (pure Python objects, no solders shim).
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Final, List

from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.rpc.api import Client
from solana.system_program import TransferParams, transfer
from solana.transaction import Transaction

# --------------------------------------------------------------------------- #
# constants & one-time globals
# --------------------------------------------------------------------------- #

log = logging.getLogger(__name__)

PING_LAMPORTS: Final[int] = 1_000          # 0.000001 SOL
THROTTLE_SEC: Final[int] = 1               # 1 request per second (public limit)
TIP_ACCOUNT: Final[PublicKey] = PublicKey(
    "11111111111111111111111111111111"
)

JITO_BUNDLE_URL: Final[str] = os.getenv(
    "JITO_BUNDLE_URL",
    "https://mainnet.block-engine.jito.wtf/rpc/v1"
)

RPC = Client("https://api.mainnet-beta.solana.com", timeout=5.0)

# -- signer ------------------------------------------------------------------ #

_KEY_PATH = Path(os.getenv("OBLIVION_KEYPAIR", "shredstream-keypair.json")).expanduser()

def _load_signer() -> Keypair:
    if not _KEY_PATH.exists():
        raise FileNotFoundError(f"keypair file not found: {_KEY_PATH}")
    raw = _KEY_PATH.read_bytes()
    if raw.startswith(b"["):
        secret = bytes(json.loads(raw))
    else:
        secret = raw
    return Keypair.from_secret_key(secret)

SOLANA_SIGNER: Final[Keypair] = _load_signer()
log.info("PingStrategy using signer: %s", SOLANA_SIGNER.public_key)

# --------------------------------------------------------------------------- #
# helper to POST a bundle via JSON-RPC v1
# --------------------------------------------------------------------------- #

import httpx   # import here to keep top clean

async def _post_bundle(b64_txs: List[str], reference: str | None = None) -> Any:
    payload = {
        "jsonrpc": "2.0",
        "id":      1,
        "method":  "send_bundle",
        "params":  [{
            "transactions": b64_txs,
            "simulation":   False,
            "reference":    reference,
        }],
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.post(JITO_BUNDLE_URL, json=payload)
        if r.status_code != 200:
            log.warning("Jito status %s %s", r.status_code, r.text)
            r.raise_for_status()
        return r.json()

# --------------------------------------------------------------------------- #
# main Strategy object
# --------------------------------------------------------------------------- #

_last_sent = 0.0                              # global throttle timestamp

class Strategy:
    """Minimal Strategy interface expected by SynergyConductor."""

    # ---- conductor calls --------------------------------------------------- #

    async def decide(self, *_a, **_kw) -> None:      # noqa: D401,E501
        """SynergyConductor passes (state, tick_ts) – we ignore for now."""
        return await self.tick()                     # thin wrapper

    # ----------------------------------------------------------------------- #
    async def tick(self) -> None:
        global _last_sent

        now = time.time()
        if now - _last_sent < THROTTLE_SEC:
            return
        _last_sent = now

        try:
            # 1) fresh block-hash (string)
            bh_resp   = RPC.get_latest_blockhash()
            recent_bh = str(bh_resp.value.blockhash)

            # 2) build transfer ix
            ix = transfer(
                TransferParams(
                    from_pubkey = SOLANA_SIGNER.public_key,
                    to_pubkey   = TIP_ACCOUNT,
                    lamports    = PING_LAMPORTS,
                )
            )

            # 3) assemble & sign tx
            tx = Transaction(
                recent_blockhash = recent_bh,
                fee_payer        = SOLANA_SIGNER.public_key,
            )
            tx.add(ix)
            tx.sign(SOLANA_SIGNER)

            # 4) base-64 encode for Jito bundle
            b64_tx = base64.b64encode(tx.serialize()).decode()

            # 5) POST bundle (respect 1 rps public limit via our throttle)
            resp = await _post_bundle([b64_tx], reference="ping-hb")
            log.info("[ping] bundle accepted: %s", resp)

        except Exception as exc:                        # noqa: BLE001
            log.warning("[ping] bundle submit failed: %s", exc)
