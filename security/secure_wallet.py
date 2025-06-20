"""
Secure signing helpers + Jito bundle submit.

* sign_and_send() — still used by legacy exec_mesh stubs
* send_bundle(tx, tip_lamports=10_000) — NEW
"""
import os, json, base58, aiohttp, asyncio, random, time
from typing import Dict, Any, List

# ✅ Compat patch for solana-py 0.29+
try:
    # ≥ 0.29.0 — Keypair lives in the solders shim
    from solders.keypair import Keypair
except ModuleNotFoundError:
    # < 0.29.0 fallback (older projects / CI images)
    from solana.keypair import Keypair

from solana.rpc.types import TxOpts
from solana.transaction import Transaction
try:  # ≥ 0.29
    from solders.instruction import Instruction as TransactionInstruction
    from solders.instruction import AccountMeta
except ModuleNotFoundError:  # fallback for older solana‑py
    from solana.transaction import TransactionInstruction, AccountMeta

from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient

_RPC = os.getenv("SOLANA_RPC", "https://api.mainnet-beta.solana.com")
_JITO_RELAY = os.getenv(
    "JITO_RELAY",
    "https://mainnet.block-engine.jito.wtf/api/v1/bundles",
)

# Jito public tip accounts (2024‑06‑01 doc)
_JITO_TIPS: List[str] = [
    "4ACfpUFoasD9bPFdeu0sBt89gBENTEHBCXAis87hNDE5",
    "D2Ly9F2TzmmrTKP2gaZMkhdUewKcT2y1Vhx8uzvZNz3",
    "9bnzA8sRgqhaNLn2b7bK8bgevBk1EzMc0BYq3B0m3sta",
    "5vyw1vSk2eMhmbRfRSXkoAdspHBJw8Rh8taXO3x3xnDn",
    "2nyhGdwKc3ZRV2gcYrY5aPVdAnF0uj3iKCsx7JhfE9yb",
]

###########################################################
# signing helpers                                         #
###########################################################

def _load_kp(path: str | os.PathLike) -> Keypair:
    with open(path, "rb") as fh:
        return Keypair.from_secret_key(fh.read())

async def sign_and_send(tx: Transaction, kp: Keypair) -> str:
    async with AsyncClient(_RPC) as cli:
        tx.recent_blockhash = (await cli.get_latest_blockhash()).value.blockhash
        tx.sign(kp)
        sig = await cli.send_raw_transaction(bytes(tx), TxOpts(skip_preflight=True))
        return str(sig.value)

###########################################################
# NEW – bundle builder / submitter                        #
###########################################################

async def send_bundle(
    raw_tx: bytes,
    payer: Keypair,
    tip_lamports: int = 10_000,
    session: aiohttp.ClientSession | None = None,
) -> Dict[str, Any]:
    """
    Build a 1‑tx bundle that:
      1. transfers `tip_lamports` to a random Jito tip acct
      2. includes the caller‑supplied tx (already signed)

    Returns {'result': ..., 'status_code': ...}
    """
    # 1) build tip‑transfer ix
    tip_acct = Pubkey.from_string(random.choice(_JITO_TIPS))
    ix = TransactionInstruction(
        program_id=Pubkey.from_string("11111111111111111111111111111111"),  # system
        data=bytes([2, 0, 0, 0, *tip_lamports.to_bytes(8, "little")]),       # transfer
        keys=[
            AccountMeta(pubkey=payer.public_key, is_signer=True, is_writable=True),
            AccountMeta(pubkey=tip_acct, is_signer=False, is_writable=True),
        ],
    )
    tip_tx = Transaction()
    tip_tx.add(ix)
    tip_tx.recent_blockhash = "0" * 32  # placeholder, BE ignores BH when bundle‑only
    tip_tx.sign(payer)

    bundle = [base58.b58encode(bytes(tip_tx)).decode(),
              base58.b58encode(raw_tx).decode()]

    payload = {"bundle": bundle}
    headers = {"Content-Type": "application/json"}

    close_me = False
    if session is None:
        session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=3))
        close_me = True

    try:
        async with session.post(_JITO_RELAY, json=payload, headers=headers) as resp:
            txt = await resp.text()
            return {"status_code": resp.status, "result": txt}
    finally:
        if close_me:
            await session.close()
