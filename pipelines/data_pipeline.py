# pipelines/data_pipeline.py
"""
Phase 9-C  ·  Market data pipeline
────────────────────────────────────────────────────────────────────────────
• loads  config/watchlist.json      → list[str] SPL mints
• filters tokens through Rug-Checker
• fetches live prices (Birdeye /defi/price) per SAFE token
• exposes:
      fetch_prices()          -> {mint: price}
      fetch_market_snapshot() -> {sol_price, token_prices, timestamp}
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List

import requests

# ─── paths ────────────────────────────────────────────────────────────────
_REPO_ROOT = Path(__file__).resolve().parents[1]
_SECRETS   = _REPO_ROOT / "config" / "secrets.json"
_WATCHLIST = _REPO_ROOT / "config" / "watchlist.json"

# ─── constants ────────────────────────────────────────────────────────────
_SOL_MINT  = "So11111111111111111111111111111111111111112"
_BIRDEYE   = "https://public-api.birdeye.so/defi/price"

# ─── API-key ──────────────────────────────────────────────────────────────
_API_KEY: str | None = None
def _load_api_key() -> None:
    global _API_KEY
    if _API_KEY is not None:
        return
    try:
        _API_KEY = json.loads(_SECRETS.read_text())["birdeye_api_key"]
    except Exception:
        _API_KEY = None

# ─── watch-list loader ────────────────────────────────────────────────────
def _load_watchlist() -> List[str]:
    try:
        mints: List[str] = json.loads(_WATCHLIST.read_text())
        return mints or [_SOL_MINT]
    except Exception:
        return [_SOL_MINT]

# ─── RUG-CHECK integration ────────────────────────────────────────────────
from security.rug_checker import rug_check
from security.secure_wallet import get_solana_client

_RPC = get_solana_client("mainnet")
_VERDICT_CACHE: dict[str, str] = {}

def _filter_safe_tokens(mints: List[str]) -> List[str]:
    safe: List[str] = []
    for m in mints:
        verdict = _VERDICT_CACHE.get(m)
        if verdict is None:
            verdict = rug_check(m, _RPC)
            _VERDICT_CACHE[m] = verdict
            print(f"[RugCheck] {m[:4]}… verdict → {verdict}")
        if verdict == "SAFE":
            safe.append(m)
    return safe

# ─── price cache ──────────────────────────────────────────────────────────
_PRICE: Dict[str, float] = {}          # mint → last price
_COOL_OFF: Dict[str, float] = {}       # mint → 429 retry-after ts
_MIN_POLL = 5                          # seconds between calls per mint

def _fetch_price(mint: str) -> None:
    """
    Update _PRICE[mint] in-place.  Handles 429 & empty payloads.
    """
    import time

    # 429 back-off ----------------------------------------------------------
    if mint in _COOL_OFF and time.time() < _COOL_OFF[mint]:
        return

    headers = {"X-API-KEY": _API_KEY} if _API_KEY else {}
    try:
        r = requests.get(_BIRDEYE, params={"address": mint}, headers=headers, timeout=4)
        if r.status_code == 429:
            print(f"[DataPipeline] Birdeye 429 for {mint[:4]}… – cooling 60 s")
            _COOL_OFF[mint] = time.time() + 60
            return
        r.raise_for_status()
        val = r.json()["data"]["value"]      # may KeyError
        _PRICE[mint] = float(val)
        if mint == _SOL_MINT:
            print(f"[DataPipeline] Live SOL price: {val:.2f}")
    except KeyError:
        print(f"[DataPipeline] Birdeye {mint[:4]}… err → KeyError('value')")
    except Exception as exc:                 # noqa: BLE001
        print(f"[DataPipeline] Birdeye fetch {mint[:4]}… failed → {exc!r}")

def _refresh_prices() -> None:
    """
    Refresh SAFE tokens, keeping a per-mint 5 s throttle.
    """
    _load_api_key()
    mints = _filter_safe_tokens(_load_watchlist())

    now = time.time()
    for m in mints:
        if now - _COOL_OFF.get(m, 0) < 0:     # still cooling
            continue
        if now - _PRICE.get(f"{m}_ts", 0) < _MIN_POLL:
            continue
        _fetch_price(m)
        _PRICE[f"{m}_ts"] = now

# ─── public helpers ───────────────────────────────────────────────────────
def fetch_prices() -> Dict[str, float]:
    _refresh_prices()
    return {k: v for k, v in _PRICE.items() if not k.endswith("_ts")}

def fetch_market_snapshot() -> Dict:
    prices = fetch_prices()
    sol    = prices.get(_SOL_MINT, 0.0)
    return {
        "sol_price": sol,
        "token_prices": prices,
        "timestamp": time.time(),
    }

# legacy alias for older code
fetch_sol_price = fetch_market_snapshot

def data_pipeline_init() -> None:
    print("[DataPipeline] Initialized.")
