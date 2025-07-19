import os, httpx, json, time
_TS = os.getenv("TIMESCALE_URL", "http://localhost:9000")
async def write(table: str, row: dict):
    async with httpx.AsyncClient(timeout=1.0) as c:
        await c.post(f"{_TS}/write", json={"table": table, "data": row})
