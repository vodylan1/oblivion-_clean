# security/rug_checker.py
"""
Cheap honeypot / rug-pull filter (on-chain only).

Public API
----------
verdict = rug_check(mint_addr: str, client: Client)
          -> "SAFE" | "WARN" | "BLOCK"
"""

from __future__ import annotations
import json
import time
from pathlib import Path

# ── PublicKey shim ───────────────────────────────────────────────────────
try:                                      # ➊ solana-py present
    from solana.publickey import PublicKey  # type: ignore
    def _to_pubkey(s: str) -> PublicKey:
        return PublicKey(s)
except ModuleNotFoundError:               # ➋ fallback to solders
    from solders.pubkey import Pubkey as _Pub
    def _to_pubkey(s: str) -> _Pub:
        return _Pub.from_string(s)

from solana.rpc.api import Client         # solana-py is still required

# ── constants & configuration ────────────────────────────────────────────
# Wrapped-SOL mint – never rug-checked
_KNOWN_SAFE = {
    "So11111111111111111111111111111111111111112",          # wSOL
}

# Optional user whitelist  config/whitelist.json  (["mint1", "mint2", …])
_WL_PATH = Path(__file__).resolve().parents[1] / "config" / "whitelist.json"
try:
    _KNOWN_SAFE.update(json.loads(_WL_PATH.read_text()))
except FileNotFoundError:
    pass
except json.JSONDecodeError as err:
    print(f"[RugCheck] Malformed whitelist.json – {err}")

_MIN_LP_SOL       = 50       # < 50 SOL liquidity → WARN / BLOCK
_WARN_SELL_TAX_P  = 8
_BLOCK_SELL_TAX_P = 15

_CACHE   : dict[str, str]  = {}
_TS      : dict[str, float] = {}
_TTL_S   = 3600


# ── helpers ──────────────────────────────────────────────────────────────
def _get_transfer_fee_pct(client: Client, mint) -> int:
    """Return sell-tax % or −1 on RPC failure."""
    try:
        info = client.get_account_info(mint, commitment="confirmed")["result"]["value"]
        if not info:
            return -1
        raw = info["data"][0]
        data = raw.encode("utf-8")
        if len(data) < 38:
            return 0
        fee_bps = int.from_bytes(data[36:38], "little")
        return fee_bps // 100
    except Exception:      # noqa: BLE001
        return -1


def _lp_liquidity_sol(client: Client, mint) -> float:
    try:
        resp = client.get_token_largest_accounts(mint)["result"]["value"]
        lamports = sum(int(a["uiAmountString"].split(".")[0]) for a in resp[:3])
        return lamports / 1e9
    except Exception:
        return 0.0


# ── public API ───────────────────────────────────────────────────────────
def rug_check(mint_addr: str, client: Client) -> str:
    """
    Very fast, cached risk verdict.
    * "SAFE"  – looks legitimate
    * "WARN"  – suspicious (high tax or thin LP)
    * "BLOCK" – honeypot / not liquid / errors
    """

    # 0. whitelist fast-path ------------------------------------------------
    if mint_addr in _KNOWN_SAFE:
        return "SAFE"

    # 1. cache --------------------------------------------------------------
    now = time.time()
    if mint_addr in _CACHE and now - _TS[mint_addr] < _TTL_S:
        return _CACHE[mint_addr]

    verdict = "SAFE"
    mint    = _to_pubkey(mint_addr)

    # 2. sell-tax heuristic -------------------------------------------------
    fee = _get_transfer_fee_pct(client, mint)
    if fee == -1:
        verdict = "WARN"
    elif fee >= _BLOCK_SELL_TAX_P:
        verdict = "BLOCK"
    elif fee >= _WARN_SELL_TAX_P:
        verdict = "WARN"

    # 3. LP liquidity heuristic --------------------------------------------
    lp = _lp_liquidity_sol(client, mint)
    if lp == 0:
        verdict = "BLOCK"
    elif lp < _MIN_LP_SOL and verdict != "BLOCK":
        verdict = "WARN"

    _CACHE[mint_addr] = verdict
    _TS[mint_addr]    = now
    return verdict
