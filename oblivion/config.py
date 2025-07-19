
import os
def price_db_path() -> str:
    return os.getenv("OBLIVION_PRICE_DB", "./data/price_queue.db")
MAX_PRICE_AGE_MS = 300
