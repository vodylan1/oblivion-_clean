from pipelines.price_feed import sol_usd


def test_ci_price_stub():
    # CI env var is set by pytest.ini; price feed must return deterministic stub
    assert sol_usd() == 125.0
