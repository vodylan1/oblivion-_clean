"""
security.secure_wallet
──────────────────────
Build, sign, and POST searcher bundles to Jito Block-Engine (mainnet).

Key points
----------
* solana-py 0.28  + solders 0.10.x
* Bundles encoded **base-64**
* JSON-RPC 2.0 envelope  ➜  method = "sendBundle"
* Debug print dumps response body on HTTP ≥ 400
* `Keypair` alias exported for legacy callers
"""

from __future__ import annotations
import os, json, base64, backoff, httpx
from typing import Sequence, List

# ── solders primitives ────────────────────────────────────────────────
from solders.keypair      import Keypair as SoldersKeypair
from solders.pubkey       import Pubkey
from solders.instruction  import Instruction
from solders.system_program import TransferParams, transfer

# ── solana-py 0.28 wrapper for Transaction ────────────────────────────
from solana.transaction   import Transaction, TransactionInstruction

# ----------------------------------------------------------------------
# Back-compat export
# ----------------------------------------------------------------------
Keypair = SoldersKeypair  # legacy: pipelines.jito_submit expects this symbol

# ----------------------------------------------------------------------
# Config
# ----------------------------------------------------------------------
JITO_ENDPOINT = os.getenv(
    "JITO_BUNDLE_URL",
    "https://mainnet.block-engine.jito.wtf/api/v1/bundles",
)

KEYFILE = os.getenv("OBLIVION_KEYPAIR", "shredstream-keypair.json")
SIGNER: SoldersKeypair = SoldersKeypair.from_bytes(
    bytes(json.load(open(KEYFILE, "r", encoding="utf-8")))
)

TIP_DEST = Pubkey.from_string(
    os.getenv("OBLIVION_PING_TIP", "11111111111111111111111111111111")
)

# ----------------------------------------------------------------------
# Helper builders
# ----------------------------------------------------------------------
def _tip_ix(lamports: int) -> Instruction:
    params = TransferParams(
        from_pubkey=SIGNER.pubkey(),
        to_pubkey=TIP_DEST,
        lamports=lamports,
    )
    return transfer(params)


def _build_signed_tx(ixs: Sequence[Instruction]) -> bytes:
    tx = Transaction()
    for ix in ixs:
        tx.add(TransactionInstruction.from_solders(ix))
    tx.sign(SIGNER)
    return tx.serialize()

# ----------------------------------------------------------------------
# Network POST with back-off + debug dump
# ----------------------------------------------------------------------
@backoff.on_exception(
    backoff.expo,
    (httpx.HTTPStatusError,),
    max_time=30,
    giveup=lambda e: e.response.status_code not in (429,),
)
async def _post_bundle(raw_tx: bytes) -> dict:
    b64 = base64.b64encode(raw_tx).decode("ascii")

    payload = {
        "jsonrpc": "2.0",
        "id":       1,
        "method":   "sendBundle",
        "params": {
            "transactions": [b64],
            "simulation":   False,
        },
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(JITO_ENDPOINT, json=payload, timeout=10)

        if resp.status_code >= 400:          # debug aid
            print("Jito status", resp.status_code, resp.text[:400])

        resp.raise_for_status()
        return resp.json()

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
async def send_bundle(raw_tx: bytes, _signer: SoldersKeypair, *, tip_lamports=0):
    """Legacy wrapper (tip ignored)."""
    return await _post_bundle(raw_tx)


async def sign_and_send(ix_list: List[Instruction], tip_lamports: int = 0):
    """
    Build a Transaction from solders instructions, append optional tip,
    sign with module signer, submit to Jito.
    """
    ixs = list(ix_list)
    if tip_lamports:
        ixs.append(_tip_ix(tip_lamports))

    raw_tx = _build_signed_tx(ixs)
    return await _post_bundle(raw_tx)
