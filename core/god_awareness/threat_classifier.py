from typing import TypedDict, List
from .wallet_profiler import WalletProfiler


class Threat(TypedDict):
    token: str
    level: int          # 0‑3
    reason: str
    confidence: float   # 0‑1


class ThreatClassifier:
    """Scores tokens 0‑100 based on wallet activity & heuristics."""

    def __init__(self, profiler: WalletProfiler) -> None:
        self.profiler = profiler

    def score_token(self, token: str, wallets: List[str]) -> int:
        # Simple heuristic: dev wallet or unknown whale -> high threat
        score = 0
        for w in wallets:
            label = self.profiler.label(w)
            if label in {"rugger", "suspicious"}:
                score += 40
            elif label == "unknown":
                score += 10
        return min(score, 100)
