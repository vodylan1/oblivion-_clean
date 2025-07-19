import os

def price_db_path() -> str:
    return os.getenv("OBLIVION_PRICE_DB", "./data/price_queue.db")

MAX_PRICE_AGE_MS = 300

#  Phase‑09 additions
def birdeye_key() -> str:
    return os.getenv("BIRDEYE_API_KEY", "demo_key")

def rpc_url() -> str:
    return os.getenv(
        "OBLIVION_RPC_URL",
        "https://api.mainnet-beta.solana.com",
    )
