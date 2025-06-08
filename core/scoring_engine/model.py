"""Neural Scoring Engine v2 – 32‑feature MLP with hot‑reload."""

from __future__ import annotations

from pathlib import Path
from typing import List

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor

CHECKPOINT_DIR = Path("models/checkpoints")
LATEST_SYMLINK = CHECKPOINT_DIR / "latest.pt"


class _GatedResBlock(nn.Module):
    def __init__(self, dim: int) -> None:
        super().__init__()
        self.lin1 = nn.Linear(dim, dim)
        self.lin2 = nn.Linear(dim, dim)
        self.gate = nn.Parameter(torch.zeros(dim))

    def forward(self, x: Tensor) -> Tensor:  # noqa: D401
        y = F.silu(self.lin1(x))
        y = self.lin2(y)
        return x + torch.sigmoid(self.gate) * y


class ScoringNet(nn.Module):
    INPUT_DIM = 32
    HIDDEN = 48

    def __init__(self) -> None:
        super().__init__()
        self.fc_in = nn.Linear(self.INPUT_DIM, self.HIDDEN)
        self.res = _GatedResBlock(self.HIDDEN)
        self.fc_out = nn.Linear(self.HIDDEN, 1)

    def forward(self, x: Tensor) -> Tensor:  # noqa: D401
        h = F.relu(self.fc_in(x))
        h = self.res(h)
        return torch.sigmoid(self.fc_out(h))  # 0‑1 score


class ScoringEngine:
    """Singleton wrapper exposed to agents / conductor."""
    _INSTANCE: "ScoringEngine | None" = None

    @classmethod
    def instance(cls) -> "ScoringEngine":
        if cls._INSTANCE is None:
            cls._INSTANCE = cls()
        return cls._INSTANCE

    def __init__(self) -> None:
        self.model = ScoringNet()
        self.model.eval()
        self._last_loaded: str | None = None
        self._try_hot_reload()

    def score(self, feature_vec: List[float]) -> float:
        self._try_hot_reload()
        x = torch.tensor(feature_vec, dtype=torch.float32).unsqueeze(0)
        with torch.no_grad():
            return float(self.model(x).squeeze().clamp(0.0, 1.0))

    # internal
    def _try_hot_reload(self) -> None:
        if not LATEST_SYMLINK.exists():
            return
        ckpt = LATEST_SYMLINK.resolve()
        if ckpt.name == self._last_loaded:
            return
        self.model.load_state_dict(torch.load(ckpt, map_location="cpu"))
        self._last_loaded = ckpt.name
