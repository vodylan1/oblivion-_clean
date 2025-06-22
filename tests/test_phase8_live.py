# tests/test_phase8_live.py
import pytest
from pipelines.factor_loader import encode_features
from core.scoring_engine.model import ScoringEngine

DUMMY_SNAPSHOT = {
    "price_now": 1.05,
    "price_1h": 1.0,
    "price_24h": 0.8,
    "price_7d": 0.5,
    "min_30d": 0.5,
    "max_30d": 1.2,
    "liq_now": 25_000,
    "vol_usd_24h": 45_000,
    "tweets_per_h": 80,
    "tw_sentiment": 0.4,
}


@pytest.mark.asyncio
async def test_end_to_end_scoring():
    vec = encode_features(DUMMY_SNAPSHOT)
    score = ScoringEngine.instance().score(vec)
    assert 0 <= score <= 1
