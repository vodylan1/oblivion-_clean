from __future__ import annotations
import time, os, json, logging, backoff

# solders + solana
from solders.keypair     import Keypair       as SoldersKeypair
from solders.pubkey      import Pubkey        as SoldersPubkey
from solders.instruction import Instruction   as SoldersIx
from solana.keypair      import Keypair       as SolanaKeypair
from solana.transaction  import Transaction

# project helpers
from agents                import TradeSignal
from utils.solana          import transfer_sol_ix
from security.secure_wallet import send_bundle

log = logging.getLogger(__name__)

# ── load secret once, derive both keypair flavours ────────────────────
KEYFILE = os.getenv("OBLIVION_KEYPAIR", "shredstream-keypair.json")
secret_bytes = bytes(json.load(open(KEYFILE, "r", encoding="utf-8")))

SOLDERS_SIGNER = SoldersKeypair.from_bytes(secret_bytes)          # .pubkey()
SOLANA_SIGNER  = SolanaKeypair.from_secret_key(secret_bytes)      # .public_key

log.info("PingStrategy using signer: %s", SOLDERS_SIGNER.pubkey())

# ── constants ─────────────────────────────────────────────────────────
PING_INTERVAL = 5.0
DUMMY_TIP     = 1_000                                            # lamports
TIP_ACCOUNT   = SoldersPubkey.from_string(
    os.getenv("OBLIVION_PING_TIP", "11111111111111111111111111111111")
)

# ── back-off wrapper around bundle submission ─────────────────────────
@backoff.on_exception(
    backoff.expo, (Exception,), max_time=30,
    giveup=lambda e: getattr(e, "status_code", 0) not in (429,),
)
async def _safe_send(raw_tx: bytes):
    # send_bundle expects a signer with .pubkey() → give it the solders one
    await send_bundle(raw_tx, SOLDERS_SIGNER, tip_lamports=DUMMY_TIP)

# ── heartbeat strategy ────────────────────────────────────────────────
class Strategy:
    """Every 5 s: build & submit a 0.000001 SOL tip bundle."""

    def __init__(self):
        self._last = 0.0

    async def decide(self, _tick) -> TradeSignal | None:
        now = time.time()
        if now - self._last < PING_INTERVAL:
            return None
        self._last = now

        log.info("ping tick ➜ %s", time.strftime("%H:%M:%S"))

        # solders instruction
        ix: SoldersIx = transfer_sol_ix(
            from_pubkey=SOLDERS_SIGNER.pubkey(),
            to_pubkey  =TIP_ACCOUNT,
            lamports   =DUMMY_TIP,
        )

        # wrap, sign, serialize
        tx = Transaction()
        tx.add(ix)                     # solana-py 0.29 accepts solders Ix
        tx.sign(SOLANA_SIGNER)         # needs .public_key & .secret_key

        try:
            await _safe_send(tx.serialize())
            log.info("[ping] bundle sent OK")
        except Exception as exc:
            log.warning("[ping] bundle submit failed: %s", exc)

        return TradeSignal(action="HOLD", confidence=0.01, meta={"src": "ping"})
