import json, asyncio
from pathlib import Path
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient

RPC = "https://api.mainnet-beta.solana.com"


async def main():
    wallets = json.loads(Path("wallets/stealth_pool.json").read_text())["wallets"]
    async with AsyncClient(RPC) as client:
        for w in wallets:
            key = Pubkey.from_string(w["pubkey"])
            lamports = (await client.get_balance(key)).value
            print(f'{w["name"]:<10s}  {lamports/1e9:6.2f} SOL')


if __name__ == "__main__":
    asyncio.run(main())
