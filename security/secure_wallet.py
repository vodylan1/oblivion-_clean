"""
security.secure_wallet
──────────────────────
Helpers to build, sign, and submit Jito bundles.

* Uses solders 0.10.x (required by solana-py 0.28)
* Encodes each bundle entry as **base-64** per Jito’s REST API
* Exposes a `Keypair` alias for back-compat (`pipelines.jito_submit`)
"""

from __future__ import annotations
import os, json, base64, backoff, httpx
from typing import Sequence, List

# solders (used throughout)
from solders.keypair      import Keypair as SoldersKeypair
from solders.pubkey       import Pubkey
from solders.instruction  import Instruction
from solders.system_program import ID as SYSTEM_ID, TransferParams, transfer

# solana-py 0.28 for Transaction wrapper
from solana.transaction import Transaction

# ----------------------------------------------------------------------
# Back-compat: let older code `from security.secure_wallet import Keypair`
# ----------------------------------------------------------------------
Keypair = SoldersKeypair  # <- three-line alias resolves ImportError

# ----------------------------------------------------------------------
# Config ----------------------------------------------------------------
JITO_ENDPOINT = os.getenv(
    "JITO_BUNDLE_URL",
    "https://bundles.block-engine.jito.wtf/api/v1/bundles",
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
    """Return solders SystemProgram::Transfer instruction."""
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
    tx.sign(SIGNER)  # solana-py wrapper accepts solders signer
    return tx.serialize()


@backoff.on_exception(
    backoff.expo,
    (httpx.HTTPStatusError,),
    max_time=30,
    giveup=lambda e: e.response.status_code not in (429,),
)
async def _post_bundle(raw_tx: bytes) -> dict:
    """POST a single-tx bundle to Jito; raw_tx must be signed/serialized."""
    b64 = base64.b64encode(raw_tx).decode("ascii")
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            JITO_ENDPOINT,
            json={"bundle": [b64], "simulate": False},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

# ----------------------------------------------------------------------
# Public API ------------------------------------------------------------
async def send_bundle(raw_tx: bytes, _signer: SoldersKeypair, *, tip_lamports=0):
    """Legacy shim (pipelines.jito_submit). Simply forwards to _post_bundle."""
    return await _post_bundle(raw_tx)


async def sign_and_send(ix_list: List[Instruction], tip_lamports: int = 0):
    """
    Convenience: build a Transaction from solders instructions,
    append an optional tip, sign with SIGNER, and submit.
    """
    ixs = list(ix_list)
    if tip_lamports:
        ixs.append(_tip_ix(tip_lamports))
    raw_tx = _build_signed_tx(ixs)
    return await _post_bundle(raw_tx)
