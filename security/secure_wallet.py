"""
security.secure_wallet
──────────────────────
Helpers to build, sign, and submit bundles to Jito Block-Engine.

✓ solders 0.10.x (matches solana-py 0.28)
✓ base-64-encoded transactions
✓ `Keypair` alias for legacy callers (`pipelines.jito_submit`)
✓ POST payload uses **"transactions"** field (v1 API)
"""

from __future__ import annotations
import os, json, base64, backoff, httpx
from typing import Sequence, List

# ── solders (crypto primitives) ───────────────────────────
from solders.keypair      import Keypair as SoldersKeypair
from solders.pubkey       import Pubkey
from solders.instruction  import Instruction
from solders.system_program import TransferParams, transfer

# ── solana-py 0.28 (transaction wrapper) ─────────────────
from solana.transaction import Transaction, TransactionInstruction

# ----------------------------------------------------------------------
# Back-compat export: older code may `from security.secure_wallet import Keypair`
# ----------------------------------------------------------------------
Keypair = SoldersKeypair

# ----------------------------------------------------------------------
# Config ----------------------------------------------------------------
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
# Helpers ----------------------------------------------------------------
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


@backoff.on_exception(
    backoff.expo,
    (httpx.HTTPStatusError,),
    max_time=30,
    giveup=lambda e: e.response.status_code not in (429,),
)
async def _post_bundle(raw_tx: bytes) -> dict:
    """
    Send a single-tx bundle.

    Jito v1 expects:
        { "transactions": ["<base64_tx>"], "simulate": false }
    """
    b64 = base64.b64encode(raw_tx).decode("ascii")
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            JITO_ENDPOINT,
            json={"transactions": [b64], "simulate": False},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

# ----------------------------------------------------------------------
# Public API ------------------------------------------------------------
async def send_bundle(raw_tx: bytes, _signer: SoldersKeypair, *, tip_lamports=0):
    """Legacy wrapper — tip is ignored here; handled by caller if needed."""
    return await _post_bundle(raw_tx)


async def sign_and_send(ix_list: List[Instruction], tip_lamports: int = 0):
    """
    Build a Transaction from solders instructions, append optional tip,
    sign with the module signer, and submit to Jito.
    """
    ixs = list(ix_list)
    if tip_lamports:
        ixs.append(_tip_ix(tip_lamports))
    raw_tx = _build_signed_tx(ixs)
    return await _post_bundle(raw_tx)
