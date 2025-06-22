import os, aiohttp, asyncio, json

_RELAY = os.getenv("HELIUS_PRIVATE", "https://rpc.helius.xyz/v1/private")
_KEY = os.getenv("HELIUS_API_KEY", "")


async def send_private(tx_bytes: bytes) -> str:
    if not _KEY:
        raise RuntimeError("HELIUS_API_KEY missing")
    headers = {"x-api-key": _KEY}
    async with aiohttp.ClientSession() as sess:
        async with sess.post(_RELAY, headers=headers, data=tx_bytes) as r:
            data = await r.json()
            if r.status != 200:
                raise RuntimeError(f"Helius {r.status}: {data}")
            return data["signature"]
