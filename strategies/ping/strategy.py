from __future__ import annotations
import time, os, json, logging, backoff
from solana.keypair      import Keypair
from solana.transaction  import Transaction

from agents                import TradeSignal
from utils.solana          import transfer_sol_ix
from security.secure_wallet import send_bundle

log = logging.getLogger(__name__)

# ── signer ─────────────────────────────────────────────────────────────
KEYFILE = os.getenv("OBLIVION_KEYPAIR", "shredstream-keypair.json")
secret_bytes = bytes(json.load(open(KEYFILE, "r", encoding="utf-8")))
SIGNER = Keypair.from_secret_key(secret_bytes)
log.info("PingStrategy using signer: %s", SIGNER.public_key)

# ── config ─────────────────────────────────────────────────────────────
PING_INTERVAL = 5.0                      # seconds
DUMMY_TIP     = 1_000                    # lamports (0.000001 SOL)
TIP_ACCOUNT   = os.getenv(
    "OBLIVION_PING_TIP",
    "11111111111111111111111111111111"
)  # Base58 string

@backoff.on_exception(
    backoff.expo, (Exception,), max_time=30,
    giveup=lambda e: getattr(e, "status_code", 0) not in (429,),
)
async def _safe_send(raw_tx: bytes):
    await send_bundle(raw_tx, SIGNER, tip_lamports=DUMMY_TIP)

class Strategy:
    """Heartbeat – every 5 s sends a dust-transfer bundle."""

    def __init__(self):
        self._last = 0.0

    async def decide(self, _tick) -> TradeSignal | None:
        now = time.time()
        if now - self._last < PING_INTERVAL:
            return None
        self._last = now

        log.info("ping tick ➜ %s", time.strftime("%H:%M:%S"))

        # build a solders Instruction via helper, passing Base58 strings
        ix = transfer_sol_ix(
            from_pubkey=str(SIGNER.public_key),
            to_pubkey  =TIP_ACCOUNT,
            lamports   =DUMMY_TIP,
        )

        tx = Transaction()
        tx.add(ix)
        tx.sign(SIGNER)

        try:
            await _safe_send(tx.serialize())
            log.info("[ping] bundle sent OK")
        except Exception as exc:
            log.warning("[ping] bundle submit failed: %s", exc)

        return TradeSignal(action="HOLD", confidence=0.01, meta={"src": "ping"})
