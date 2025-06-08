import os
import time
from functools import wraps
from typing import Callable, TypeVar

T = TypeVar("T")
_ENABLED = os.getenv("EXPERIMENTAL_LATENCY_PROFILER", "false").lower() == "true"


def profiled(fn: Callable[..., T]) -> Callable[..., T]:
    if not _ENABLED:
        return fn

    @wraps(fn)
    def wrapper(*args, **kwargs):
        t0 = time.perf_counter()
        out = fn(*args, **kwargs)
        dt = (time.perf_counter() - t0) * 1000
        print(f"[latency] {fn.__qualname__}: {dt:.2f} ms")
        return out

    return wrapper
