"""
LLM autopatch scheduler stub.
Enable via EXPERIMENTAL_LLM_SCHEDULER=true
"""

import asyncio
import os
from datetime import timedelta

FLAG = os.getenv("EXPERIMENTAL_LLM_SCHEDULER", "false").lower() == "true"
INTERVAL_MIN = int(os.getenv("LLM_SCHED_MINUTES", "240"))  # default 4 h


async def run(loop_fn):
    if not FLAG:
        return
    while True:
        await loop_fn()
        await asyncio.sleep(timedelta(minutes=INTERVAL_MIN).total_seconds())
