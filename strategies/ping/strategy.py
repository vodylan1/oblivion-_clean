"""
PingStrategy -- minimal heartbeat that sends a 0.000001 SOL transfer
inside a Jito bundle every ≈1 second.  Pure solana-py (v0.28) only;
no solders API calls in this module.

Prerequisites
-------------
• ENV  OBLIVION_KEYPAIR   → path to 64-byte JSON array keypair file
• ENV  HELIUS_HTTP        → HTTPS RPC endpoint (defaults to public Helius)
• ENV  JITO_BUNDLE_URL    → https://mainnet.block-engine.jito.wtf/api/v1/bundles
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import pathlib
import time
from typing import Any, List

from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.rpc.async_api import AsyncClient
from solana.system_program import TransferParams, transfer
from solana.transaction import Transaction

from security.secure_wallet import send_bundle

LAMPORTS_PER_SOL = 1_000_000_000
TIP_ACCOUNT = PublicKey("11111111111111111111111111111111")  # <-- replace!

_HELIUS_HTTP = os.getenv("HELIUS_HTTP", "https://api.mainnet.helius-rpc.com")
_RPC = AsyncClient(_HELIUS_HTTP, timeout=4)

_log = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------


def _load_keypair(path: str | os.PathLike[str]) -> Keypair:
    """Read a Solana CLI JSON keypair (64-byte array) and return Keypair."""
    arr: List[int]
    with open(path, encoding="utf-8") as f:
        arr = json.load(f)
    if not isinstance(arr, list) or len(arr) != 64:
        raise ValueError("invalid keypair JSON (need 64 ints)")
    return Keypair.from_secret_key(bytes(arr))


# ----------------------------------------------------------------------
# Strategy object expected by SynergyConductor
# ----------------------------------------------------------------------


class Strategy:
    def __init__(self) -> None:
        keyfile = os.getenv("OBLIVION_KEYPAIR", "shredstream-keypair.json")
        if not pathlib.Path(keyfile).exists():
            raise FileNotFoundError(
                f"Keypair file '{keyfile}' not found -- set OBLIVION_KEYPAIR env"
            )

        self.signer: Keypair = _load_keypair(keyfile)
        self.fee_payer: PublicKey = self.signer.public_key
        self._last_sent: float = 0.0  # throttle 1 req/s

        _log.info("PingStrategy using signer: %s", self.fee_payer)

    # SynergyConductor calls `.decide()` each tick; we throttle internally.
    async def decide(self, *_a: Any, **_kw: Any) -> None:
        if time.time() - self._last_sent < 1.05:
            return  # 1 req/s public limit
        self._last_sent = time.time()
        await self._heartbeat()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    async def _heartbeat(self) -> None:
        try:
            bh_resp = await _RPC.get_latest_blockhash()
            blockhash = str(bh_resp.value.blockhash)  # Hash → str

            tx = self._build_tx(blockhash)
            b64_tx = base64.b64encode(tx.serialize()).decode()

            ok = send_bundle([b64_tx])  # secure_wallet handles JSON-RPC POST
            if ok:
                _log.info("✅ ping bundle accepted by Jito")
            else:
                _log.warning("❌ ping bundle rejected (see logs above)")
        except Exception as exc:  # broad catch so the loop never crashes
            _log.warning("[ping] bundle submit failed: %s", exc)

    def _build_tx(self, recent_blockhash: str) -> Transaction:
        """Create, sign, and return a SystemProgram.transfer transaction."""
        ix = transfer(
            TransferParams(
                from_pubkey=self.fee_payer,
                to_pubkey=TIP_ACCOUNT,
                lamports=1_000,  # 0.000001 SOL
            )
        )
        tx = Transaction(recent_blockhash=recent_blockhash, fee_payer=self.fee_payer)
        tx.add(ix)
        tx.sign(self.signer)
        return tx
