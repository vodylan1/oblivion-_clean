from core.god_awareness.wallet_profiler import WalletProfiler
from core.god_awareness.threat_classifier import ThreatClassifier

def test_threat_score_basic():
    profiler = WalletProfiler()
    profiler._cache["W1"] = {"label": "rugger", "pnl": 0, "tx_count": 1}
    tc = ThreatClassifier(profiler)
    score = tc.score_token("XYZ", ["W1", "W2"])
    assert score >= 40
