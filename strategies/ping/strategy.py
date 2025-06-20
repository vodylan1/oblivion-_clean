"""
PingStrategy – heartbeat every ≈5 s.
Builds a 0.000001 SOL transfer and sends it to the Jito bundle RPC.
"""

from __future__ import annotations
import json, logging, os, time
from pathlib import Path

from solana.rpc.api        import Client
from solana.transaction    import Transaction
from solana.keypair        import Keypair as SolanaKeypair
from solana.publickey      import PublicKey
from solana.system_program import TransferParams, transfer

from security.secure_wallet import KEYFILE, sign_and_send

log = logging.getLogger(__name__)
RPC = Client("https://api.mainnet-beta.solana.com")

TIP_ACCOUNT   = PublicKey("11111111111111111111111111111111")    # TODO real tip
PING_LAMPORTS = int(os.getenv("PING_LAMPORTS", "1000"))           # 0.000001 SOL
THROTTLE_SEC  = 1.05                                              # 1 req/s

# ------------------------------------------------------------------ #
# Load signer from the same JSON key-file used elsewhere
# ------------------------------------------------------------------ #
with open(Path(KEYFILE), "r", encoding="utf-8") as f:
    secret_bytes = bytes(json.load(f))
SOLANA_SIGNER = SolanaKeypair.from_secret_key(secret_bytes)

_last_sent: float = 0.0


class Strategy:                              # loaded by SynergyConductor
    name = "ping"

    # -------------------------------------------------------------- #
    # main heartbeat
    # -------------------------------------------------------------- #
    def tick(self) -> None:
        global _last_sent
        now = time.time()
        if now - _last_sent < THROTTLE_SEC:
            return                          # respect public Jito limit
        _last_sent = now

        try:
            # 1) recent hash (cast Hash -> str)
            bh_resp   = RPC.get_latest_blockhash()
            recent_bh = str(bh_resp.value.blockhash)

            # 2) build instruction
            ix = transfer(
                TransferParams(
                    from_pubkey=SOLANA_SIGNER.public_key,
                    to_pubkey=TIP_ACCOUNT,
                    lamports=PING_LAMPORTS,
                )
            )

            # 3) assemble + sign
            tx = Transaction(recent_blockhash=recent_bh,
                             fee_payer=SOLANA_SIGNER.public_key)
            tx.add(ix)
            tx.sign(SOLANA_SIGNER)

            log.info("ping tick ➜ %s", time.strftime("%H:%M:%S"))
            resp = sign_and_send(tx, reference="ping-hb")
            log.info("[ping] bundle accepted: %s", resp)

        except Exception as exc:            # noqa: BLE001
            log.warning("[ping] bundle submit failed: %s", exc)

    # -------------------------------------------------------------- #
    # Conductor expects async decide(*args, **kwargs)
    # -------------------------------------------------------------- #
    async def decide(self, *args, **kwargs):    # type: ignore[override]
        self.tick()
        return None
