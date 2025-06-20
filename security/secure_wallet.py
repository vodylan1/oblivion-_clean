"""
security.secure_wallet
──────────────────────
Build / sign transactions and post bundles to Jito (solana‑py 0.28).
"""

from __future__ import annotations
import os, json, backoff, httpx, base64
from typing import Sequence, List

from solders.keypair      import Keypair   as SoldersKeypair
from solders.pubkey       import Pubkey
from solders.instruction  import Instruction
from solders.system_program import ID as SYSTEM_ID, TransferParams, transfer
from solana.transaction   import Transaction

JITO_ENDPOINT = os.getenv(
    "JITO_BUNDLE_URL",
    "https://bundles.block-engine.jito.wtf/api/v1/bundles"
)

KEYFILE = os.getenv("OBLIVION_KEYPAIR", "shredstream-keypair.json")
SIGNER  = SoldersKeypair.from_bytes(bytes(json.load(open(KEYFILE))))

TIP_DEST = Pubkey.from_string(
    os.getenv("OBLIVION_PING_TIP", "11111111111111111111111111111111")
)

# ── helpers ───────────────────────────────────────────────────────────
def _tip_ix(lamports: int) -> Instruction:
    params = TransferParams(
        from_pubkey=SIGNER.pubkey(),
        to_pubkey  =TIP_DEST,
        lamports   =lamports,
    )
    return transfer(params)

def _build_signed_tx(ixs: Sequence[Instruction]) -> bytes:
    tx = Transaction()
    for ix in ixs:
        tx.add(ix)
    tx.sign(SIGNER)
    return tx.serialize()

@backoff.on_exception(
    backoff.expo,
    (httpx.HTTPStatusError,),
    max_time=30,
    giveup=lambda e: e.response.status_code not in (429,),
)
async def _post_bundle(raw_tx: bytes) -> dict:
    b64 = base64.b64encode(raw_tx).decode("ascii")
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            JITO_ENDPOINT,
            json={"bundle": [b64], "simulate": False},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

# ── public API ────────────────────────────────────────────────────────
async def send_bundle(raw_tx: bytes, _signer: SoldersKeypair, *, tip_lamports=0):
    return await _post_bundle(raw_tx)

async def sign_and_send(ix_list: List[Instruction], tip_lamports: int = 0):
    ixs = list(ix_list)
    if tip_lamports:
        ixs.append(_tip_ix(tip_lamports))
    raw_tx = _build_signed_tx(ixs)
    return await _post_bundle(raw_tx)
