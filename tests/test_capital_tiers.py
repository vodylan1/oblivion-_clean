import pytest
from core.capital_manager.capital_class import classify_equity, CapitalTier
from core.capital_manager.adaptive_strategy import apply_tier_overrides

def test_classify():
    assert classify_equity(1_000) is CapitalTier.MICRO
    assert classify_equity(6_000) is CapitalTier.SMALL
    assert classify_equity(40_000) is CapitalTier.MID
    assert classify_equity(150_000) is CapitalTier.LARGE
    assert classify_equity(700_000) is CapitalTier.WHALE

def test_overrides():
    p = apply_tier_overrides({}, CapitalTier.SMALL)
    assert p["max_trade_usd"] == 1_000
    assert p["slip_bps"] < 250
