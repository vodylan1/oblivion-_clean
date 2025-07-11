"""Helius price-feed helper (Phase-7).

Usage:
    >>> from pipelines.price_feed import sol_usd
    >>> price = sol_usd()

During CI a constant *125 USD* is returned so the test-suite is deterministic.
"""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Final

_HELIUS_KEY: Final[str] = os.getenv("HELIUS_API_KEY")
_URL: Final[str] = (
    f"https://api.helius.xyz/v0/price?api-key={_HELIUS_KEY}" if _HELIUS_KEY else ""
)


def sol_usd() -> float:
    """Return the current SOL->USD price.

    * CI / missing API key → 125 $ (stub).
    * Prod               → fetch from Helius.
    """
    if os.getenv("CI") or not _HELIUS_KEY:
        return 125.0

    with urllib.request.urlopen(_URL, timeout=4) as resp:
        data = json.load(resp)
    return float(data["solPrice"])
