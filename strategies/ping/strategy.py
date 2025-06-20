"""
PingStrategy – heartbeat every ≈5 s:
* builds a 0.000001 SOL transfer to the tip-address (placeholder)
* signs it and ships to Jito via secure_wallet.sign_and_send()
"""

from __future__ import annotations
import asyncio, base64, logging, os, time

from solana.rpc.api             import Client
from solana.transaction         import Transaction
from solana.keypair             import Keypair
from solana.system_program      import TransferParams, transfer
from security.secure_wallet     import SIGNER, sign_and_send

log = logging.getLogger(__name__)
RPC = Client("https://api.mainnet-beta.solana.com")

TIP_ACCOUNT = "11111111111111111111111111111111"   # TODO replace with real

# --------------------------------------------------------------------------- #
#  Throttle (public 1 req / s limit)
# --------------------------------------------------------------------------- #

_last_sent: float = 0.0


class Strategy:       # loaded by SynergyConductor
    name = "ping"

    def tick(self) -> None:
        global _last_sent

        now = time.time()
        if now - _last_sent < 1.05:           # stay under 1 req / s
            return
        _last_sent = now

        try:
            recent = RPC.get_latest_blockhash()["result"]["value"]["blockhash"]
            ix = transfer(
                TransferParams(
                    from_pubkey=SIGNER.pubkey(),
                    to_pubkey=TIP_ACCOUNT,
                    lamports=1_000,          # 0.000001 SOL
                )
            )
            tx = Transaction(recent_blockhash=recent, fee_payer=SIGNER.pubkey())
            tx.add(ix)
            tx.sign(SIGNER)

            # encode   -------------------------------------------------------
            b64_tx = base64.b64encode(bytes(tx)).decode()
            log.info("ping tick ➜ %s", time.strftime("%H:%M:%S"))
            resp = sign_and_send(tx, reference="ping-hb")
            log.info("[ping] bundle accepted: %s", resp)

        except Exception as exc:              # noqa: BLE001
            log.warning("[ping] bundle submit failed: %s", exc)
