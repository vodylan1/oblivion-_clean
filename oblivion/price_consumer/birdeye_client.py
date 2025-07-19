import os, httpx, asyncio, time
from oblivion.core.models import PriceSample
from oblivion.config import birdeye_key

URL = "https://openapi.birdeye.so/public/price?address=So11111111111111111111111111111111111111112"

async def fetch_price() -> PriceSample:
    headers = {"X-API-KEY": birdeye_key()}
    async with httpx.AsyncClient(timeout=0.4) as client:
        r = await client.get(URL, headers=headers)
        data = r.json()["data"]
        return PriceSample(timestamp_ns=time.time_ns(), price=float(data["value"]))
