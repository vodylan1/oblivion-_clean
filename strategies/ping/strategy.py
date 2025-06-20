from __future__ import annotations
import time
import backoff

# ── compatibility shims ────────────────────────────────────────────────
try:  # solana-py ≥ 0.29
    from solders.instruction import Instruction as TransactionInstruction
except ModuleNotFoundError:             # solana-py ≤ 0.28
    from solana.transaction import TransactionInstruction

try:                                     # solana-py ≥ 0.29
    from solders.pubkey import Pubkey as PublicKey
except ModuleNotFoundError:              # solana-py ≤ 0.28
    from solana.publickey import PublicKey

# ── project imports ───────────────────────────────────────────────────
from agents import TradeSignal
from security.secure_wallet import sign_and_send as original_sign_and_send

# ---------------------------------------------------------------------
# transfer helper (stub for now)
# ---------------------------------------------------------------------
# Replace with:     from utils.solana import transfer_sol_ix
def transfer_sol_ix(*_a, **_kw):   # noqa: D401,E501
    """Stub – returns None until utils.solana helper is implemented."""
    return None

# ── config ────────────────────────────────────────────────────────────
TIP_ACCOUNT = PublicKey.from_string("11111111111111111111111111111111")  # TODO: real addr
PING_INTERVAL = 5.0            # seconds
DUMMY_TIP = 1_000              # 0.000001 SOL

# ── backoff-wrapped sender ────────────────────────────────────────────
@backoff.on_exception(
    backoff.expo,
    (Exception,),
    max_time=30,
    giveup=lambda e: not hasattr(e, "response") or e.response.status_code not in (429,),
)
async def sign_and_send(ix_list: list[TransactionInstruction]):
    return await original_sign_and_send(ix_list)

# ── strategy object ───────────────────────────────────────────────────
class Strategy:
    """Ping (heartbeat) strategy – submits a dust transfer every 5 s."""

    def __init__(self):
        self._last = 0.0

    async def decide(self, _tick) -> TradeSignal | None:
        now = time.time()
        if now - self._last < PING_INTERVAL:
            return None
        self._last = now

        # --------------------------------------------------------------
        # Build bundle only if helper returns a real Instruction object
        # (stub returns None during early bootstrap)
        # --------------------------------------------------------------
        ix = transfer_sol_ix(
            wallet_pubkey=getattr(_tick, "wallet", None),   # may be None in stub mode
            dest_pubkey=TIP_ACCOUNT,
            lamports=DUMMY_TIP,
        )

        if ix is None:  # helper not implemented yet → skip quietly
            return TradeSignal(action="HOLD", confidence=0.01,
                               meta={"src": "ping-stub"})

        try:
            await sign_and_send([ix])
        except Exception as exc:
            print("[ping] bundle submit failed:", exc)

        return TradeSignal(action="HOLD", confidence=0.01, meta={"src": "ping"})
