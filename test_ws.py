import asyncio
import aiohttp

HELIUS_KEY = "e702ea0c-f586-4cc6-b2b0-e488fb5358b8"
WS_URL = f"wss://stream.helius.xyz/v0/solana/mainnet?api-key={HELIUS_KEY}"

async def test_connection():
    async with aiohttp.ClientSession() as session:
        try:
            async with session.ws_connect(WS_URL, timeout=10) as ws:
                print("✅ Connection successful")
        except Exception as e:
            print("❌ Connection failed:", e)

asyncio.run(test_connection())
