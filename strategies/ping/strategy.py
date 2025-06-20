from __future__ import annotations
import time, os, json, logging, backoff, pathlib

# ── solders & solana imports ───────────────────────────────────────────
from solders.keypair     import Keypair
from solders.pubkey      import Pubkey as PublicKey
from solders.instruction import Instruction as SoldersIx
from solana.transaction  import Transaction
try:                                           # solana-py ≥ 0.29
    from solana.instruction import Instruction as TransactionInstruction
except ImportError:                            # ≤ 0.28 fallback
    from solana.transaction import TransactionInstruction

from agents                import TradeSignal
from utils.solana          import transfer_sol_ix
from security.secure_wallet import send_bundle

log = logging.getLogger(__name__)

# ── signer keypair (JSON array file) ───────────────────────────────────
KEYFILE = os.getenv("OBLIVION_KEYPAIR", "shredstream-keypair.json")
secret_bytes = bytes(json.load(open(KEYFILE, "r", encoding="utf-8")))
SIGNER       = Keypair.from_bytes(secret_bytes)
log.info("PingStrategy using signer: %s", SIGNER.pubkey())

# ── constants ─────────────────────────────────────────────────────────
PING_INTERVAL = 5.0
DUMMY_TIP     = 1_000
TIP_ACCOUNT   = PublicKey.from_string(
    os.getenv("OBLIVION_PING_TIP", "11111111111111111111111111111111")
)

@backoff.on_exception(
    backoff.expo, (Exception,), max_time=30,
    giveup=lambda e: getattr(e, "status_code", 0) not in (429,),
)
async def _safe_send(raw_tx: bytes):
    await send_bundle(raw_tx, SIGNER, tip_lamports=DUMMY_TIP)

class Strategy:
    def __init__(self):
        self._last = 0.0

    async def decide(self, _tick) -> TradeSignal | None:
        now = time.time()
        if now - self._last < PING_INTERVAL:
            return None
        self._last = now

        log.info("ping tick ➜ %s", time.strftime("%H:%M:%S"))

        ix_sold: SoldersIx = transfer_sol_i_
