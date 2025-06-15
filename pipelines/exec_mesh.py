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
    relay_url: str = "https://jito.block-engine.solana.com",
) -> str:
    """
    MEV bundle submission for `atomic_arb` strategy.
    """
    tx: Any = {"type": "bundle", "len": len(bundle), "relay": relay_url}
    try:
        sig = await sign_and_send(tx, relay_url)
    except Exception as exc:
        print("[exec_mesh] bundle error:", exc)
        sig = _fake_sig()
    return sig
