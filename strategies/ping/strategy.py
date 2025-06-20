# strategies/ping/strategy.py
import asyncio, base64, os, time
from datetime import datetime
from typing import List

import httpx
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.transaction import Transaction, TransactionInstruction, AccountMeta
from solana.rpc.async_api import AsyncClient
from solana.system_program import SYS_PROGRAM_ID, TransferParams, transfer

# ──────────────────────────────────────────────────────────────
# ░░  CONFIG  ░░
# ──────────────────────────────────────────────────────────────
JITO_URL   = os.getenv("JITO_BUNDLE_URL",
                       "https://mainnet.block-engine.jito.wtf/api/v1/bundles")
HELIUS_RPC = os.getenv(
    "HELIUS_HTTP",
    # plain-solana RPC works for block-hashes; use your own Helius key if you have one
    "https://api.mainnet-beta.solana.com",
)
KEYFILE    = os.getenv("OBLIVION_KEYPAIR", "shredstream-keypair.json")
LAMPORTS   = 1_000                            # 0.000001 SOL “heartbeat”
TICK_SEC   = 1.0                              # 1 req/s – respect Jito public limit
# -----------------------------------------------------------------

# build signer
with open(KEYFILE, "r", encoding="utf-8") as f:
    secret = bytes(__import__("json").load(f))
SIGNER: Keypair = Keypair.from_secret_key(secret)

TIP_ACCOUNT = PublicKey("11111111111111111111111111111111")  # replace later

# lazily shared clients
_RPC  = AsyncClient(HELIUS_RPC, timeout=10)
_HTTP = httpx.AsyncClient(base_url=JITO_URL, timeout=10)

# ──────────────────────────────────────────────────────────────
# ░░  UTILS  ░░
# ──────────────────────────────────────────────────────────────
async def _recent_blockhash() -> str:
    """Return recent blockhash **as plain str** (solana-py expects str)."""
    resp = await _RPC.get_latest_blockhash()
    return str(resp.value.blockhash)          # ← cast fixes Hash→str error


def _build_ping_tx(blockhash: str) -> Transaction:
    """1 lamport transfer from the signer to the TIP_ACCOUNT."""
    ix = transfer(
        TransferParams(
            from_pubkey=SIGNER.public_key,
            to_pubkey=TIP_ACCOUNT,
            lamports=LAMPORTS,
        )
    )
    tx              = Transaction(recent_blockhash=blockhash)
    tx.add(ix)
    tx.sign(SIGNER)
    return tx


async def _send_bundle(txs: List[Transaction]) -> httpx.Response:
    """POST to /bundles; returns the raw httpx Response."""
    payload = {
        "transactions": [base64.b64encode(tx.serialize()).decode() for tx in txs],
        "simulation":   False,
    }
    return await _HTTP.post("", json=payload)   # empty path → /bundles


# ──────────────────────────────────────────────────────────────
# ░░  STRATEGY CLASS  ░░
# ──────────────────────────────────────────────────────────────
class Strategy:
    """Minimal heartbeat strategy compatible with SynergyConductor."""

    def __init__(self):
        print(f"[ping] signer: {SIGNER.public_key}")
        self._last = 0.0                       # last bundle UNIX-ts

    async def decide(self, *_a, **_kw):
        """Called every loop by the conductor."""
        if time.time() - self._last < TICK_SEC:
            return None
        self._last = time.time()

        try:
            bh   = await _recent_blockhash()
            tx   = _build_ping_tx(bh)
            resp = await _send_bundle([tx])

            # Jito returns 202 Accepted on success / queue
            print("[ping] Jito status", resp.status_code, resp.text[:120])
        except Exception as exc:
            print("[ping] bundle submit failed:", exc)


# clean shutdown helpers (optional, keeps linters happy)
async def _shutdown():
    await _RPC.close()
    await _HTTP.aclose()

