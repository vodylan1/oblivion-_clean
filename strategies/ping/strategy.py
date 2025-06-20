from __future__ import annotations
import time
import logging
import backoff
import os

# ── logging ────────────────────────────────────────────────────────────
log = logging.getLogger(__name__)

# ── compatibility shims (solana-py ≥ 0.29 vs ≤ 0.28) ───────────────────
try:  # solana-py ≥ 0.29
    from solders.instruction import Instruction as TransactionInstruction
    from solders.pubkey import Pubkey as PublicKey
except ModuleNotFoundError:          # solana-py ≤ 0.28
    from solana.transaction import TransactionInstruction
    from solana.publickey import PublicKey

from solana.transaction import Transaction
from security.secure_wallet import (
    send_bundle,             # bundles + tip transfer
    Keypair,                 # signer
)
from utils.solana import transfer_sol_ix       # ← real helper now in use
from agents import TradeSignal

# ── config ─────────────────────────────────────────────────────────────
PING_INTERVAL = 5.0                     # seconds
DUMMY_TIP     = 1_000                   # 0.000001 SOL
TIP_ACCOUNT   = PublicKey.from_string(
    os.getenv("OBLIVION_PING_TIP", "11111111111111111111111111111111")
)

# ---- load signer once -------------------------------------------------
#   Priv-key file path comes from env or default ./oblivion_key.json
#   (make sure this key has enough lamports for 0.000001 SOL tips)
KEYFILE = os.getenv("OBLIVION_KEYPAIR", "oblivion_key.json")
SIGNER: Keypair = Keypair.from_secret_key(open(KEYFILE, "rb").read())

# ── back-off wrapper around send_bundle ────────────────────────────────
@backoff.on_exception(
    backoff.expo,
    (Exception,),
    max_time=30,
    giveup=lambda e: getattr(e, "status_code", 0) not in (429,),
)
async def _safe_send(raw_tx: bytes):
    await send_bundle(raw_tx, SIGNER, tip_lamports=DUMMY_TIP)

# ── Strategy class ─────────────────────────────────────────────────────
class Strategy:
    """Heartbeat strategy → every 5 s send a 0.000001 SOL tip bundle."""

    def __init__(self):
        self._last = 0.0

    async def decide(self, _tick) -> TradeSignal | None:
        now = time.time()
        if now - self._last < PING_INTERVAL:
            return None
        self._last = now

        # console heartbeat
        log.info("ping tick @ %s", time.strftime("%H:%M:%S"))

        # build transfer instruction (SystemProgram::Transfer)
        ix: TransactionInstruction = transfer_sol_ix(
            from_pubkey=SIGNER.public_key,   # sender
            to_pubkey=TIP_ACCOUNT,           # receiver
            lamports=DUMMY_TIP,
        )

        # wrap in Transaction and sign
        tx = Transaction()
        tx.add(ix)
        tx.sign(SIGNER)

        # submit via secure_wallet.send_bundle()
        try:
            await _safe_send(bytes(tx))
            log.info("[ping] bundle sent OK")
        except Exception as exc:
            log.warning("[ping] bundle submit failed: %s", exc)

        # still emit a HOLD signal so the conductor logs something
        return TradeSignal(action="HOLD", confidence=0.01, meta={"src": "ping"})
