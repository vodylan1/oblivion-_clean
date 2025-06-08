"""
PyTorch MLP skeleton for Neural Scoring Engine v2
Input  : 32‑dim feature vector (see docs/factor_spec.md)
Output : score 0 – 100  (float tensor shape [N, 1])
"""

import torch
import torch.nn as nn


class ScoringModel(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(32, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid(),  # → 0‑1
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:  # type: ignore
        return self.net(x) * 100.0  # map to 0‑100
