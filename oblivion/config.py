import os

def jupiter_key() -> str:
    return os.getenv("JUPITER_API_KEY", "demo_key")
