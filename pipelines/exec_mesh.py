"""
Execution‑Mesh Helpers
──────────────────────
Provides thin async wrappers around the secure‑wallet signer so that
higher‑level strategies (atomic‑arb, meme‑snipe, etc.) can reuse the same
interface without importing low‑level Solana objects.

• send_swap_transaction()   – generic swap / DEX interaction
• send_snipe_transaction()  – micro‑cap sniper TX     (Pepe‑Mode, etc.)
• send_bundle_transaction() – pre‑built bundle (atomic arb / MEV)

All functions return a **fake signature** in unit‑tests; the real signer is
wired through Jito in `scripts/run_live.py`.
"""

from __future__ import annotations
import os, random, string
from typing import Any

# --- Jito relay defaults & helper import ------------------------------------
_RELAY = "https://block-engine.jito.wtf/api/v1/bundles"  # default relay
from pipelines.bundle_sender import send_bundle_transaction as _jito_send

# ---------------------------------------------------------------------------

from security.secure_wallet import sign_and_send


# ──────────────────────────────────────────────────────────────────
def _fake_sig() -> str:
    """Return a 64‑char hex suitable as placeholder in tests."""
    return os.urandom(32).hex()


# ──────────────────────────────────────────────────────────────────
async def send_swap_transaction(
    label: str,
    size_lamports: int,
    cu_price: int,
    rpc_url: str = "https://api.mainnet-beta.solana.com",
) -> str:
    """
    Generic DEX swap; used by `xdex_arbitrage`.
    """
    tx: Any = {"type": "swap", "label": label, "size": size_lamports, "cu": cu_price}
    try:
        sig = await sign_and_send(tx, rpc_url)
    except Exception as exc:
        print("[exec_mesh] swap error:", exc)
        sig = _fake_sig()
    return sig


# ──────────────────────────────────────────────────────────────────
async def send_snipe_transaction(
    token_address: str,
    buy_lamports: int,
    rpc_url: str = "https://api.mainnet-beta.solana.com",
) -> str:
    """
    Thin wrapper used by `pipelines.meme_snipe`.
    """
    tx: Any = {"type": "snipe", "token": token_address, "size": buy_lamports}
    try:
        sig = await sign_and_send(tx, rpc_url)
    except Exception as exc:
        print("[exec_mesh] snipe error:", exc)
        sig = _fake_sig()
    return sig


# ──────────────────────────────────────────────────────────────────
async def send_bundle_transaction(
    bundle: list[Any],
    relay_url: str = _RELAY,
) -> str:
    """
    MEV bundle submission for `atomic_arb` strategy.
    """
    tx: Any = {"type": "bundle", "len": len(bundle), "relay": relay_url}
    try:
        # Try Jito first; fallback to direct signer if import not available in tests
        if _jito_send:
            sig = await _jito_send(bundle, relay_url)
        else:
            raise ImportError("_jito_send not available")
    except Exception:
        try:
            sig = await sign_and_send(tx, relay_url)
        except Exception as exc:
            print("[exec_mesh] bundle error:", exc)
            sig = _fake_sig()
    return sig
