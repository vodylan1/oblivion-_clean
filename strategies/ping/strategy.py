"""
PingStrategy – sends a 1‑lamport “heartbeat” bundle every 90 s
so that the Jito success/fail counters and Discord metrics are exercised.

It costs ~0.000000001 SOL per run; negligible compared to production trading.
"""
from __future__ import annotations
import time, base64

from agents import TradeSignal
from security.secure_wallet import sign_and_send


_DEST = "11111111111111111111111111111111"  # SystemProgram address (burn)


class Strategy:
    def __init__(self, period: float = 90.0):
        self._period = period
        self._last   = 0.0

    # --------------------------------------------------------------------- #
    async def decide(self, _market_tick: dict | None = None) -> TradeSignal | None:
        now = time.time()
        if now - self._last < self._period:
            return None                     # too soon – skip

        self._last = now

        # ------------------------------------------------------------------
        # Build a placeholder tx – here we just encode the string "PING"
        # so sign_and_send() still produces a real bundle and the relay
        # responds with 200 OK (or error).  Replace by a real Tx later.
        raw_tx_b64 = base64.b64encode(b"PING").decode()

        try:
            await sign_and_send(raw_tx_b64)     # metrics counted inside
        except Exception as exc:
            # soft‑fail so the conductor continues polling
            print("[ping] bundle submit failed:", exc)

        return TradeSignal(
            action="HOLD",
            confidence=0.01,
            meta={"src": "ping", "ts": int(now)},
        )
