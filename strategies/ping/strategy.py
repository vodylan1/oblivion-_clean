from __future__ import annotations
import asyncio, base64, json, logging, os, time
from typing import Final

from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.rpc.async_api import AsyncClient
from solana.system_program import SYS_PROGRAM_ID, TransferParams, transfer
from solana.transaction import Transaction

from security.secure_wallet import send_bundle

LAMPORTS_PER_SOL: Final[int] = 1_000_000_000
KEYFILE: Final[str] = os.environ.get("OBLIVION_KEYPAIR", "shredstream-keypair.json")
RPC_URL: Final[str] = os.environ.get(
    "SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com"
)
JITO_MIN_INTERVAL: Final[float] = 1.10
TIP_ACCOUNT: Final[PublicKey] = PublicKey("11111111111111111111111111111111")

log = logging.getLogger(__name__)


def _load_signer(path: str) -> Keypair:
    with open(path, "r", encoding="utf-8") as f:
        secret = bytes(json.load(f))
    return Keypair.from_secret_key(secret)


SIGNER: Final[Keypair] = _load_signer(KEYFILE)
SIGNER_PUB: Final[PublicKey] = SIGNER.public_key
log.info("PingStrategy using signer: %s", SIGNER_PUB)


class Strategy:
    _last_bundle_ts: float = 0.0

    async def decide(self, *_a, **_kw):
        try:
            await self._tick_impl()
        except Exception as exc:
            log.warning("[ping] bundle submit failed: %s", exc, exc_info=False)

    async def _tick_impl(self) -> None:
        now = time.time()
        if now - self._last_bundle_ts < JITO_MIN_INTERVAL:
            return

        async with AsyncClient(RPC_URL) as rpc:
            resp = await rpc.get_latest_blockhash()
            recent_blockhash: str = str(resp.value.blockhash)

        ix = transfer(
            TransferParams(
                from_pubkey=SIGNER_PUB,
                to_pubkey=TIP_ACCOUNT,
                lamports=1_000,
            )
        )

        tx = Transaction(recent_blockhash=recent_blockhash, fee_payer=SIGNER_PUB)
        tx.add(ix)
        tx.sign(SIGNER)

        b64_tx = base64.b64encode(tx.serialize()).decode()

        ok = send_bundle([b64_tx], simulate=False)   # ← reference removed
        if ok:
            log.info("[ping] bundle sent OK – %s", int(now))
            self._last_bundle_ts = now
