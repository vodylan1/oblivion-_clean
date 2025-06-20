from __future__ import annotations
import time, os, json, logging, backoff
from solders.keypair     import Keypair
from solders.pubkey      import Pubkey   as PublicKey
from solders.instruction import Instruction as SoldersIx
from solana.transaction  import Transaction

from agents                import TradeSignal
from utils.solana          import transfer_sol_ix
from security.secure_wallet import send_bundle

log = logging.getLogger(__name__)

# ── signer keypair (JSON array created via solana-keygen) ──────────────
KEYFILE = os.getenv("OBLIVION_KEYPAIR", "shredstream-keypair.json")
secret_bytes = bytes(json.load(open(KEYFILE, "r", encoding="utf-8")))
_sold_kp     = Keypair.from_bytes(secret_bytes)

class _CompatSigner:
    """Expose .public_key and .secret_key for solana-py Transaction.sign()."""
    def __init__(self, kp: Keypair, raw: bytes):
        self._kp = kp
        self._raw = raw
    @property
    def public_key(self):   # solana-py expects this attr
        return self._kp.pubkey()
    @property
    def secret_key(self):   # 64-byte (sk+pk) for solana-py signing
        return self._raw

SIGNER = _CompatSigner(_sold_kp, secret_bytes)
log.info("PingStrategy using signer: %s", SIGNER.public_key)

# ── constants ─────────────────────────────────────────────────────────
PING_INTERVAL = 5.0                      # seconds between heartbeats
DUMMY_TIP     = 1_000                    # lamports (0.000001 SOL)
TIP_ACCOUNT   = PublicKey.from_string(
    os.getenv("OBLIVION_PING_TIP", "11111111111111111111111111111111")
)

# ── back-off wrapper for Jito bundle submission ───────────────────────
@backoff.on_exception(
    backoff.expo, (Exception,), max_time=30,
    giveup=lambda e: getattr(e, "status_code", 0) not in (429,),
)
async def _safe_send(raw_tx: bytes):
    await send_bundle(raw_tx, SIGNER, tip_lamports=DUMMY_TIP)

# ── heartbeat strategy ────────────────────────────────────────────────
class Strategy:
    """Every 5 s: build & send a tiny tip bundle; log heartbeat."""

    def __init__(self):
        self._last = 0.0

    async def decide(self, _tick) -> TradeSignal | None:
        now = time.time()
        if now - self._last < PING_INTERVAL:
            return None
        self._last = now

        log.info("ping tick ➜ %s", time.strftime("%H:%M:%S"))

        # build solders instruction
        ix: SoldersIx = transfer_sol_ix(
            from_pubkey=SIGNER.public_key,
            to_pubkey  =TIP_ACCOUNT,
            lamports   =DUMMY_TIP,
        )

        # wrap, sign, serialise
        tx = Transaction()
        tx.add(ix)                # solana-py 0.29 accepts solders Ix
        tx.sign(SIGNER)

        try:
            await _safe_send(tx.serialize())
            log.info("[ping] bundle sent OK")
        except Exception as exc:
            log.warning("[ping] bundle submit failed: %s", exc)

        return TradeSignal(action="HOLD", confidence=0.01, meta={"src": "ping"})
