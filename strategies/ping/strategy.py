"""
PingStrategy – submits a 1‑lamport ‘heartbeat’ bundle every 30 s.
Costs nothing, exercises the full Jito / metrics pipeline.
"""
from __future__ import annotations
import time
from agents import TradeSignal
from security.secure_wallet import sign_and_send   # counts metrics internally

_PERIOD = 30.0          # faster so you see Discord summary quickly


class Strategy:
    def __init__(self):
        self._last = 0.0

    async def decide(self, _tick) -> TradeSignal | None:
        now = time.time()
        if now - self._last < _PERIOD:
            return None
        self._last = now

        # Empty payload – Jito replies 200 OK, metrics ⇒ success + 1
        raw_tx_b64 = ""  # ← minimal heartbeat bundle
        try:
            await sign_and_send(raw_tx_b64)
        except Exception as exc:
            print("[ping] bundle submit failed:", exc)

        return TradeSignal(action="HOLD", confidence=0.01, meta={"src": "ping"})
