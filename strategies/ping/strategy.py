"""
PingStrategy – heartbeat every ≈5 s.
Builds a tiny transfer, signs it, and ships it to Jito Block‑Engine.
"""

from __future__ import annotations
import logging, os, time

from solana.rpc.api        import Client
from solana.transaction    import Transaction
from solana.system_program import TransferParams, transfer
from solana.publickey      import PublicKey

from security.secure_wallet import SIGNER, sign_and_send

log = logging.getLogger(__name__)
RPC = Client("https://api.mainnet-beta.solana.com")

TIP_ACCOUNT   = PublicKey("11111111111111111111111111111111")  # TODO real tip
PING_LAMPORTS = int(os.getenv("PING_LAMPORTS", "1000"))         # 0.000001 SOL
THROTTLE_SEC  = 1.05                                            # ≤1 req/s

_last_sent: float = 0.0


class Strategy:                         # loaded by SynergyConductor
    name = "ping"

    # ------------------------------------------------------------------ #
    # main heartbeat
    # ------------------------------------------------------------------ #
    def tick(self) -> None:
        global _last_sent
        now = time.time()
        if now - _last_sent < THROTTLE_SEC:          # public Jito limit
            return
        _last_sent = now

        try:
            # 1) recent block‑hash (solana‑py 0.28 object API)
            bh_resp   = RPC.get_latest_blockhash()
            recent_bh = bh_resp.value.blockhash

            # 2) build transfer instruction
            ix = transfer(
                TransferParams(
                    from_pubkey=SIGNER.pubkey(),
                    to_pubkey=TIP_ACCOUNT,
                    lamports=PING_LAMPORTS,
                )
            )

            # 3) assemble + sign TX
            tx = Transaction(recent_blockhash=recent_bh,
                             fee_payer=SIGNER.pubkey())
            tx.add(ix)
            tx.sign(SIGNER)

            log.info("ping tick ➜ %s", time.strftime("%H:%M:%S"))
            resp = sign_and_send(tx, reference="ping-hb")
            log.info("[ping] bundle accepted: %s", resp)

        except Exception as exc:                      # noqa: BLE001
            log.warning("[ping] bundle submit failed: %s", exc)

    # ------------------------------------------------------------------ #
    # SynergyConductor expects an **async** decide() it can await
    # ------------------------------------------------------------------ #
    async def decide(self, *args, **kwargs):          # type: ignore[override]
        self.tick()
        return None
