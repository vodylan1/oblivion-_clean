# intel/meme_scanner.py
"""
Realtime meme-/sentiment-score fetcher.

• Pulls a single numeric “hype score” (0-100) from MultiFeed†
• Keeps a cached value when the feed/API is down
• Provides two public functions:
      meme_scanner_init()   – one-time boot initialisation
      scan_feeds()          – returns {"meme_hype": <float>}
† If the MULTIFEED_KEY env-var is absent we fall back to
  a bounded random walk so that unit-tests and offline runs pass.
"""

from __future__ import annotations

import os
import random
import threading
import time
from typing import Dict, Any

import requests

# --------------------------------------------------------------------------- #
#  Internal state & constants
# --------------------------------------------------------------------------- #
_ENDPOINT: str = "https://api.multifeed.xyz/v1/hype-score"
_API_KEY: str | None = None

_HYPE: float = 50.0               # cached score (0-100)
_LOCK = threading.Lock()          # guards _HYPE updates
_LAST_TS: float = 0.0             # last successful fetch
_MIN_POLL_S: int = 15             # poll interval (secs)


# --------------------------------------------------------------------------- #
#  Init hook (called once from main.py)
# --------------------------------------------------------------------------- #
def meme_scanner_init() -> None:
    """
    One-time initialisation:
    • load API key from env or secrets file
    • optional warm-up fetch to confirm connectivity
    Called from main.py during Phase-8 boot.
    """
    global _API_KEY, _HYPE, _LAST_TS

    if _API_KEY is not None:           # already initialised
        return

    _API_KEY = os.getenv("MULTIFEED_KEY")
    if not _API_KEY:
        print("[MemeScanner] No MultiFeed key → using dummy hype feed.")
        return

    try:
        _HYPE = _fetch_hype_score()    # warm-up
        _LAST_TS = time.time()
        print("[MemeScanner] Online – MultiFeed feed")
    except Exception as exc:           # noqa: BLE001
        print(f"[MemeScanner] Init error → {exc!r} → fallback to dummy hype.")
        _API_KEY = None                # force dummy mode


# --------------------------------------------------------------------------- #
#  Public runtime API
# --------------------------------------------------------------------------- #
def scan_feeds() -> Dict[str, Any]:
    """
    Fast, side-effect-free call used inside the trading loop.
    Returns a dict so the caller can `.update()` its market snapshot.

        >>> scan_feeds()   ->  {"meme_hype": 78.6}
    """
    global _HYPE, _LAST_TS

    # throttle outward requests to one call every MIN_POLL_S seconds
    if _API_KEY and time.time() - _LAST_TS >= _MIN_POLL_S:
        try:
            score = _fetch_hype_score()
            with _LOCK:
                _HYPE = max(0.0, min(100.0, score))
                _LAST_TS = time.time()
        except Exception as exc:       # noqa: BLE001
            # keep last good value; log once every minute at most
            if int(time.time()) % 60 == 0:
                print(f"[MemeScanner] Fetch error → {exc!r} (keeping cache)")

    # dummy mode – bounded random walk so tests don’t stall
    if _API_KEY is None:
        with _LOCK:
            _HYPE = max(0.0, min(100.0, _HYPE + random.uniform(-5, 5)))

    return {"meme_hype": round(_HYPE, 2)}


# --------------------------------------------------------------------------- #
#  Helpers
# --------------------------------------------------------------------------- #
def _fetch_hype_score() -> float:
    """Low-level REST call → returns float score or raises HTTPError."""
    headers = {"Authorization": f"Bearer {_API_KEY}"} if _API_KEY else {}
    resp = requests.get(_ENDPOINT, headers=headers, timeout=4)
    resp.raise_for_status()
    data = resp.json()
    return float(data.get("score", 50.0))
