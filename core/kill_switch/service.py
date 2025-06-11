# core/kill_switch/service.py
from __future__ import annotations

import os
import time
from typing import Optional

from notifications.discord_notifier import notify_discord

AUTO_UNFREEZE_MIN = int(os.getenv("KS_AUTO_UNFREEZE_MIN", "0"))  # 0 = manual


class KillSwitch:
    _FROZEN: bool = False
    _FROZE_AT: Optional[float] = None

    @classmethod
    def frozen(cls) -> bool:
        if cls._FROZEN and AUTO_UNFREEZE_MIN:
            if time.time() - (cls._FROZE_AT or 0) > AUTO_UNFREEZE_MIN * 60:
                cls._FROZEN = False
        return cls._FROZEN

    @classmethod
    async def trip(cls, reason: str) -> None:
        if cls._FROZEN:
            return
        cls._FROZEN = True
        cls._FROZE_AT = time.time()
        # inside any alert code
          await notify_discord("⚠️ Kill-Switch armed …")

