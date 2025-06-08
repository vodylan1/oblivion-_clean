"""
Async webhook receiver for Helius alerts.
Requires: EXPERIMENTAL_HELIUS_WEBHOOK=true
"""

import asyncio
import os
from collections.abc import Awaitable, Callable

import aiohttp

WEBHOOK_PORT = int(os.getenv("HELIUS_WEBHOOK_PORT", "8088"))
_FLAG = os.getenv("EXPERIMENTAL_HELIUS_WEBHOOK", "false").lower() == "true"

_Callback = Callable[[dict], Awaitable[None]]
_on_tx: _Callback | None = None


def register_callback(cb: _Callback):
    global _on_tx
    _on_tx = cb


async def _handler(request):
    if not _FLAG:
        return aiohttp.web.Response(text="disabled")
    payload = await request.json()
    if _on_tx:
        await _on_tx(payload)
    return aiohttp.web.Response(text="ok")


async def run_server():
    if not _FLAG:
        return
    app = aiohttp.web.Application()
    app.add_routes([aiohttp.web.post("/", _handler)])
    runner = aiohttp.web.AppRunner(app)
    await runner.setup()
    site = aiohttp.web.TCPSite(runner, "0.0.0.0", WEBHOOK_PORT)
    await site.start()
    # keep alive
    while True:
        await asyncio.sleep(3600)
