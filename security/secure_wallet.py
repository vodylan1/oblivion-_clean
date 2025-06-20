"""
security.secure_wallet
──────────────────────
Build, sign, and post bundles to Jito Block-Engine (mainnet).

• solana-py 0.28 + solders 0.10.x
• Base-64 transactions
• JSON-RPC 2.0   method = "sendBundle"
• params **array**  ➜ [ { "transactions":[…], "simulation":false } ]
• Debug print dumps body on HTTP ≥ 400
• `Keypair` alias retained for legacy calls
"""

from __future__ import annotations
import os, json, base64, backoff, httpx
from typing import Sequence, List

# —— cryptography ———————————————————————————
from solders.keypair      import Keypair as SoldersKeypair
from solders.pubkey       import Pubkey
from solders.instruction  import Instruction
from solders.system_program import TransferParams, transfer

# —— solana-py transaction wrapper ——————————
from solana.transaction import Transaction, TransactionInstruction

# ----------------------------------------------------------------------
# Back-compat symbol
# ----------------------------------------------------------------------
Keypair = SoldersKeypair     # for pipelines.jito_submit

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
# Helpers
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
# Network POST
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
        "params": [
            {
                "transactions": [b64],
                "simulation":   False,
            }
        ],
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(JITO_ENDPOINT, json=payload, timeout=10)

        if resp.status_code >= 400:          # debug aid
            print("Jito status", resp.status_code, resp.text[:400])

        resp.raise_for_status()
        return resp.json()

# ----------------------------------------------------------------------
# Public façade
# ----------------------------------------------------------------------
async def send_bundle(raw_tx: bytes, _signer: SoldersKeypair, *, tip_lamports=0):
    """Legacy helper preserved for pipelines.jito_submit."""
    return await _post_bundle(raw_tx)


async def sign_and_send(ix_list: List[Instruction], tip_lamports: int = 0):
    """
    Compose a signed Transaction from solders instructions, append tip,
    and submit to Jito.
    """
    ixs = list(ix_list)
    if tip_lamports:
        ixs.append(_tip_ix(tip_lamports))

    raw_tx = _build_signed_tx(ixs)
    return await _post_bundle(raw_tx)
