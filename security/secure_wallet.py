"""
secure_wallet.py
────────────────────────────────────────────────────────────────────────────
• load_keypair()                 – returns a solders.Keypair
• get_solana_client(network)     – honours overrides in config/secrets.json
• wallet_and_client()            – convenience tuple for Anchor / Drift

The helper is lightweight and has **zero** external dependencies beyond
`solders`, `solana-py`, and `anchorpy`.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Tuple

from anchorpy import Wallet
from solders.keypair import Keypair
from solana.rpc.api import Client

# ───────────────────────────────────────────────────────────────────────────
# Load config/secrets.json once – swallow all errors, fall back to defaults
# ───────────────────────────────────────────────────────────────────────────
_REPO_ROOT = Path(__file__).resolve().parents[2]
_CFG_PATH  = _REPO_ROOT / "config" / "secrets.json"

_CFG: dict[str, str] = {}
try:
    _CFG = json.loads(_CFG_PATH.read_text("utf-8"))
except Exception:       # noqa: BLE001  (file missing or malformed)
    _CFG = {}

# Helper for pretty banner
def _note(txt: str) -> None:
    print(f"[SecureWallet] {txt}")


# ------------------------------------------------------------------------- #
def _default_keyfile() -> str:
    return os.path.expanduser("~/.config/solana/id.json")


def load_keypair(path: str | None = None) -> Keypair:
    """
    Load a standard 64-byte Solana keypair file.
    Falls back to an **ephemeral** random keypair if the file is missing.
    """
    path = path or _default_keyfile()
    if not os.path.exists(path):
        _note(f"Keyfile {path} not found – using random key.")
        return Keypair()
    try:
        with open(path, "r", encoding="utf-8") as fh:
            secret = bytes(json.load(fh))
        return Keypair.from_bytes(secret)
    except Exception as exc:      # noqa: BLE001
        _note(f"Could not load keyfile – {exc}; using random key.")
        return Keypair()


# ------------------------------------------------------------------------- #
def _url_for(network: str) -> str:
    """
    Return the RPC URL for *network*, honouring overrides in secrets.json.
    """
    if network == "devnet":
        return _CFG.get(
            "rpc_override_devnet",
            "https://api.devnet.solana.com",
        )
    # treat anything else as main-net
    return _CFG.get(
        "rpc_override_mainnet",
        "https://api.mainnet-beta.solana.com",
    )


def get_solana_client(network: str = "devnet") -> Client:
    url = _url_for(network)
    if "helius" in url:
        _note(f"using Helius endpoint → {url}")
    return Client(url)


# ------------------------------------------------------------------------- #
def wallet_and_client(network: str = "devnet") -> Tuple[Wallet, Client]:
    """
    Convenience helper:

        >>> wallet, client = wallet_and_client("mainnet")
    """
    kp = load_keypair()
    return Wallet(kp), get_solana_client(network)
