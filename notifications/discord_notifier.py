"""
discord_notifier.py
Phase 10.1 – send trade & event notifications to Discord
"""

import os
import json
import requests

def _load_discord_webhook() -> str | None:
    try:
        data = json.load(open("config/secrets.json","r"))
        return data.get("discord_webhook")
    except:
        return None

_WEBHOOK = _load_discord_webhook()

async def notify_discord(text: str):
    if not _WEBHOOK:
        return
    payload = {"content": text}
    try:
        resp = requests.post(_WEBHOOK, json=payload, timeout=4)
        if resp.status_code not in (200,204):
            print("[discord_notifier] error:", resp.status_code, resp.text)
    except Exception as e:
        print("[discord_notifier] exc:", e)
