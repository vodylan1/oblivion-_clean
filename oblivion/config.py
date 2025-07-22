import os

# ---------- paths & constants ----------
def price_db_path() -> str:
    """SQLite ring‑buffer price DB location."""
    return os.getenv("OBLIVION_PRICE_DB", "./data/price_queue.db")

MAX_PRICE_AGE_MS = 300   # 0.3 s staleness guard

# ---------- API keys ----------
def birdeye_key() -> str:
    """Key for Birdeye REST fallback."""
    return os.getenv("BIRDEYE_API_KEY", "demo_key")

def rpc_url() -> str:
    """Primary Solana RPC endpoint."""
    return os.getenv(
        "OBLIVION_RPC_URL",
        "https://api.mainnet-beta.solana.com",
    )

def jupiter_key() -> str:
    """Partner key for Jupiter route scorer."""
    return os.getenv("JUPITER_API_KEY", "demo_key")
