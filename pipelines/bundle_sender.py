import os, aiohttp, asyncio

_RELAY = os.getenv("JITO_RELAY", "https://block-engine.jito.wtf/api/v1/bundles")
_TOKEN = os.getenv("JITO_AUTH")  # read from env, **not** secrets.json


async def send_bundle_transaction(bundle: list[bytes]) -> str:
    if not _TOKEN:
        raise RuntimeError("JITO_AUTH token missing")
    headers = {"Authorization": _TOKEN}
    async with aiohttp.ClientSession() as sess:
        async with sess.post(_RELAY, headers=headers, data=b"".join(bundle)) as r:
            data = await r.json()
            if r.status != 200:
                raise RuntimeError(f"Jito {r.status}: {data}")
            return data["signature"]
