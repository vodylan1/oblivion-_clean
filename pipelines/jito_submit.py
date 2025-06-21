"""
Simple async consumer that takes signed tx bytes from a queue,
wraps them in a tip bundle via secure_wallet.send_bundle(), and
handles 429/500 series with back‑off.

It exposes two counters:  success_cnt / fail_cnt.
pipelines.jito_metrics flushes these to Discord.
"""
import asyncio, backoff, aiohttp, logging
from typing import Optional
from security.secure_wallet import send_bundle, Keypair

log = logging.getLogger("jito_submit")

QUEUE: asyncio.Queue[bytes] = asyncio.Queue()  # populated by strategies
_success = 0
_fail = 0

# load any wallet in stealth pool as tip‑payer (they’re funded)
_tip_payer = Keypair()  # random new temp – replace with your loader if needed


@backoff.on_exception(
    backoff.expo,
    Exception,
    max_tries=5,
    giveup=lambda e: getattr(e, "status_code", 500) < 500,
    jitter=backoff.full_jitter,
)
async def _submit(tx: bytes, sess: aiohttp.ClientSession):
    global _success, _fail
    res = await send_bundle(tx, _tip_payer, session=sess)
    if res["status_code"] == 200:
        _success += 1
    else:
        _fail += 1
        raise RuntimeError(f"Jito err {res['status_code']}: {res['result'][:80]}…")


async def submitter_loop():
    async with aiohttp.ClientSession() as sess:
        while True:
            tx = await QUEUE.get()
            try:
                await _submit(tx, sess)
            except Exception as exc:
                log.warning("bundle err %s", exc)
            finally:
                QUEUE.task_done()


def metrics() -> tuple[int, int]:
    return _success, _fail
