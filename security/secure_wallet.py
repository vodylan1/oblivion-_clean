"""
security.secure_wallet
──────────────────────
Helpers to build, sign, and submit bundles to Jito Block-Engine.

✓ Uses solders 0.10.x (matches solana-py 0.28)
✓ Encodes transactions as base-64
✓ Exposes Keypair alias for legacy imports
✓ Posts with v1 schema  ➜ {"transactions":[…], "simulation":false}
✓ Prints server payload on HTTP ≥ 400 for quick debugging
"""

from __future__ import annotations
import os, json, base64, backoff, httpx
from typing import Sequence, List

# solders primitives
from solders.keypair      import Keypair as SoldersKeypair
from solders.pubkey       import Pubkey
from solders.instruction  import Instruction
from solders.system_program import TransferParams, transfer

# solana-py 0.28 container
from solana.transaction import Transaction, TransactionInstruction

# ----------------------------------------------------------------------
# Back-compat export (legacy modules import Keypair from here)
# ----------------------------------------------------------------------
Keypair = SoldersKeypair

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
    """Return SystemProgram::Transfer instruction (solders)."""
    params = TransferParams(
        from_pubkey=SIGNER.pubkey(),
        to_pubkey=TIP_DEST,
        lamports=lamports,
    )
    return transfer(params)


def _build_signed_tx(ixs: Sequence[Instruction]) -> bytes:
    """Convert solders instructions → solana Transaction, sign, serialize."""
    tx = Transaction()
    for ix in ixs:
        tx.add(TransactionInstruction.from_solders(ix))
    tx.sign(SIGNER)
    return tx.serialize()


# ----------------------------------------------------------------------
# Network post with back-off and debug dump
# ----------------------------------------------------------------------
@backoff.on_exception(
    backoff.expo,
    (httpx.HTTPStatusError,),
    max_time=30,
    giveup=lambda e: e.response.status_code not in (429,),
)
async def _post_bundle(raw_tx: bytes) -> dict:
    """POST a single-tx bundle to Jito; prints response on HTTP ≥ 400."""
    b64 = base64.b64encode(raw_tx).decode("ascii")

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            JITO_ENDPOINT,
            json={
                "transactions": [b64],   # v1 field name
                "simulation": False,    # run on-chain if True
            },
            timeout=10,
        )

        if resp.status_code >= 400:      # ← debug aid
            print("Jito status", resp.status_code, resp.text[:400])

        resp.raise_for_status()
        return resp.json()

# ----------------------------------------------------------------------
# Public API (called by strategies / pipelines)
# ----------------------------------------------------------------------
async def send_bundle(raw_tx: bytes, _signer: SoldersKeypair, *, tip_lamports=0):
    """Legacy shim kept for pipelines.jito_submit; ignores tip."""
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
