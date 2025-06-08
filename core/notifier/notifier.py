"""
core/notifier/notifier.py
────────────────────────────────────────────────────────────────────────────
Minimal helper that lets any module do:

    from core.notifier.notifier import notify
    notify("✅ something happened")

Configuration:
* `config/secrets.json` must contain a key  "webhook_url"
      {
          "api_key":       "... if you already had one ...",
          "webhook_url":   "https://discord.com/api/webhooks/…"
      }

If the file or key is missing the helper stays silent so the trading loop
never crashes.

* All paths are computed with pathlib → works from any CWD.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Final, Optional

import requests

# ─── constants ────────────────────────────────────────────────────────────
REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[2]  # two levels up
SECRETS   : Final[Path] = REPO_ROOT / "config" / "secrets.json"

_WEBHOOK: Optional[str] = None          # populated lazily
_INIT = False


# ─── internal ─────────────────────────────────────────────────────────────
def _lazy_init() -> None:
    """Load the webhook exactly once; swallow errors gracefully."""
    global _WEBHOOK, _INIT
    if _INIT:
        return

    try:
        data: dict[str, Any] = json.loads(SECRETS.read_text("utf-8"))
        _WEBHOOK = data.get("webhook_url")
        if _WEBHOOK:
            print("[Notifier] Webhook loaded ✓")
        else:
            print("[Notifier] 'webhook_url' missing → notifier disabled.")
    except FileNotFoundError:
        print("[Notifier] secrets.json missing → notifier disabled.")
    except json.JSONDecodeError as err:
        print(f"[Notifier] Malformed secrets.json → disabled.  ↳ {err}")
    finally:
        _INIT = True


def _post(payload: dict[str, Any]) -> None:
    """Fire-and-forget HTTP POST; never raise into callers."""
    try:
        resp = requests.post(_WEBHOOK, json=payload, timeout=4)
        if resp.status_code >= 400:
            print(f"[Notifier] HTTP {resp.status_code} → {resp.text!r}")
    except requests.RequestException as exc:
        print(f"[Notifier] Network error: {exc!r}")


# ─── public helpers ───────────────────────────────────────────────────────
def notify(msg: str) -> None:
    """
    Send plain text message to Discord.  If not configured → silent no-op.
    """
    _lazy_init()
    if not _WEBHOOK:
        return
    _post({"content": msg})


def notify_trade(decision: str, price: float) -> None:
    """Convenience formatting for order flow."""
    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    notify(f"**{ts}**  `{decision}` at **${price:,.2f}**")
