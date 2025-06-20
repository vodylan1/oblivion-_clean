from __future__ import annotations
import time
import backoff

# Instruction shim
try:
    from solders.instruction import Instruction as TransactionInstruction
except ModuleNotFoundError:
    from solana.transaction import TransactionInstruction

# PublicKey shim
try:
    from solders.pubkey import Pubkey as PublicKey
except ModuleNotFoundError:
    from solana.publickey import PublicKey

from agents import TradeSignal
from security.secure_wallet import sign_and_send as original_sign_and_send
# from utils.solana import transfer_sol_ix  # ← disabled for now

# temporary stub until utils.solana exists
def transfer_sol_ix(*_a, **_kw):   # noqa: D401,E501
    """Return None – ping strategy disabled until transfer helper available."""
    return None

# CONFIG
TIP_ACCOUNT = PublicKey.from_string("11111111111111111111111111111111")  # TODO: replace with real address
PING_INTERVAL = 5.0  # seconds
DUMMY_TIP = 1_000  # 0.000001 SOL

# BACKOFF WRAPPED SENDER
@backoff.on_exception(
    backoff.expo,
    (Exception,),
    max_time=30,
    giveup=lambda e: not hasattr(e, "response") or e.response.status_code not in (429,)
)
async def sign_and_send(ix_list: list[TransactionInstruction]):
    return await original_sign_and_send(ix_list)

class Strategy:
    def __init__(self):
        self._last = 0.0

    async def decide(self, _tick) -> TradeSignal | None:
        now = time.time()
        if now - self._last < PING_INTERVAL:
            return None
        self._last = now

        try:
            ix = transfer_sol_ix(wallet_pubkey=_tick.wallet, dest_pubkey=TIP_ACCOUNT, lamports=DUMMY_TIP)
            if ix:
                await sign_and_send([ix])
        except Exception as exc:
            print("[ping] bundle submit failed:", exc)

        return TradeSignal(action="HOLD", confidence=0.01, meta={"src": "ping"})
