import os, httpx, asyncio, time
from oblivion.config import jupiter_key

async def impact_score(input_amount: float) -> float:
    url = "https://quote-api.jup.ag/v6/quote"
    params = {"inputMint": "So111111111...", "outputMint": "USDC...",
              "amount": int(input_amount*1e9), "api-key": jupiter_key()}
    async with httpx.AsyncClient(timeout=1.0) as c:
        r = await c.get(url, params=params)
        data = r.json()
        return float(data["routes"][0]["outAmountUsd"]) / input_amount
