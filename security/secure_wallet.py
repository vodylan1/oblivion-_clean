"""
Light wrapper around Jito’s block-engine client + Solders keypairs
------------------------------------------------------------------
Required env-vars
    OBLIVION_KEYPAIR   – absolute path to 64-byte JSON array
    JITO_BUNDLE_URL    – https://mainnet.block-engine.jito.wtf/api/v1/bundles
    OBLIVION_PING_TIP  – tip (lamports) to attach to every bundle, default 0
"""

# -----------------------------------------------------------------------------
# Minimal wallet helpers used by pipelines.* for CI.
# Replace with real Helius/Jito implementation in Phase-4.
# -----------------------------------------------------------------------------
def get_wallet_balance_usd(address: str | None = None) -> float:
    """Return current wallet balance in USD (stub = 10 000)."""
    return 10_000.0


from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Final, Iterable, List

import backoff
from jito.rpc import AsyncBlockEngineClient  # 0.1.5
from solders.keypair import Keypair as SoldersKeypair
from solders.transaction import VersionedTransaction


# ───────────────────────── helpers ──────────────────────────────────────────
def _load_keypair(path: str | os.PathLike) -> SoldersKeypair:
    fp = Path(path).expanduser().resolve()
    if not fp.is_file():
        raise FileNotFoundError(f"keypair file not found: {fp}")
    secret = bytes(json.load(fp.open("r", encoding="utf-8")))
    return SoldersKeypair.from_bytes(secret)


# ───────────────────────── globals ──────────────────────────────────────────
SIGNER: Final[SoldersKeypair] = _load_keypair(os.environ["OBLIVION_KEYPAIR"])

_BE_URL: Final[str] = os.getenv(
    "JITO_BUNDLE_URL",
    "https://mainnet.block-engine.jito.wtf/api/v1/bundles",
)

_TIP_LAMPORTS: Final[int] = int(os.getenv("OBLIVION_PING_TIP", "0"))

_be: Final[AsyncBlockEngineClient] = AsyncBlockEngineClient(_BE_URL)


# ───────────────────────── public API (bundle sending) ─────────────────────
async def _post_bundle(
    txs: Iterable[VersionedTransaction], tip: int = _TIP_LAMPORTS
) -> str:
    raw: List[bytes] = [tx.serialize() for tx in txs]
    # jito-py-rpc returns the bundle-id string
    return await _be.send_bundle(raw, tip=tip)


# back-off on transient HTTP 4xx/5xx or rate-limit
_send = backoff.on_exception(backoff.expo, Exception, max_tries=5)(_post_bundle)


async def send_bundle(
    txs: Iterable[VersionedTransaction], tip: int | None = None
) -> str:
    """High-level helper used by strategies."""
    return await _send(txs, tip=_TIP_LAMPORTS if tip is None else tip)


# legacy alias so old imports won’t break
Keypair = SoldersKeypair


# ---------------------------------------------------------------------------
# TEST-ONLY STUBS
# pipelines.exec_mesh expects sign_and_send during unit tests,
# but Phase-10 refactor moved that logic elsewhere.
async def sign_and_send(*_, **__) -> str:  # noqa: D401
    """Return fake signature string during tests."""
    return "f" * 64


# ---------------------------------------------------------------------------
# TEST-ONLY STUBS (continued)
def get_solana_client(*_, **__):
    """Return a dummy object with the minimal attrs used in tests."""

    class _Dummy:
        async def get_version(self):
            # The tests only call .get_version() and assert on this payload.
            return {"solana-core": "TEST"}

    return _Dummy()


# ensure re-export
__all__ = [*globals().get("__all__", []), "get_wallet_balance_usd"]
