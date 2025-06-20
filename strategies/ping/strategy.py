"""
PingStrategy – heartbeat every ≈5 s; sends a tiny transfer bundle to Jito.
"""

from __future__ import annotations
import base64, logging, os, time

from solana.rpc.api        import Client
from solana.transaction    import Transaction
from solana.system_program import TransferParams, transfer

from security.secure_wallet import SIGNER, sign_and_send

log = logging.getLogger(__name__)
RPC = Client("https://api.mainnet-beta.solana.com")

TIP_ACCOUNT   = "11111111111111111111111111111111"          # TODO real tip addr
PING_LAMPORTS = int(os.getenv("PING_LAMPORTS", "1000"))     # 0.000001 SOL
THROTTLE_SEC  = 1.05                                        # ≤1 req/s

_last_sent: float = 0.0


class Strategy:                      # loaded by SynergyConductor
    name = "ping"

    def tick(self) -> None:
        global _last_sent
        now = time.time()
        if now - _last_sent < THROTTLE_SEC:
            return
        _last_sent = now

        try:
            recent = RPC.get_latest_blockhash()["result"]["value"]["blockhash"]
            ix = transfer(
                TransferParams(
                    from_pubkey=SIGNER.pubkey(),
                    to_pubkey=TIP_ACCOUNT,
                    lamports=PING_LAMPORTS,
                )
            )
            tx = Transaction(recent_blockhash=recent, fee_payer=SIGNER.pubkey())
            tx.add(ix)
            tx.sign(SIGNER)

            log.info("ping tick ➜ %s", time.strftime("%H:%M:%S"))
            resp = sign_and_send(tx, reference="ping-hb")
            log.info("[ping] bundle accepted: %s", resp)

        except Exception as exc:          # noqa: BLE001
            log.warning("[ping] bundle submit failed: %s", exc)

    # ----------------------------------------------------------
    # Conductor expects decide(*args, **kwargs)
    # ----------------------------------------------------------
    def decide(self, *args, **kwargs):    # type: ignore[override]
        return self.tick()
