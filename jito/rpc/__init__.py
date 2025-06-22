"""
Tiny test-time stub replacing `jito.rpc`.
Implements only the names used by secure_wallet.py.
"""


class AsyncBlockEngineClient:  # noqa: D101
    def __init__(self, *_, **__):  # accept arbitrary args (url, headers…)
        pass

    async def send_bundle(self, *_, **__):  # always returns dummy sig
        return "f" * 64
