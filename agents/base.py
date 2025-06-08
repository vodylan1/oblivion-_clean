# Oblivion – core agent ABC
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict
from pydantic import BaseModel


class AgentMeta(BaseModel):
    name: str
    version: str
    risk_profile: str
    description: str
    enabled: bool = True


class TradeSignal(BaseModel):
    action: str           # BUY | SELL | SHORT | CLOSE | HOLD | BUY_LOW_CONF
    confidence: float     # 0‑1
    meta: Dict[str, Any] = {}


class Agent(ABC):
    meta: AgentMeta

    @abstractmethod
    async def logic(self, market_data: Dict[str, Any]) -> TradeSignal: ...

    async def after_trade(self, result: Dict[str, Any]) -> None: ...
