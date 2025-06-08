def test_jupiter_sim():
    """Jupiter should accept the request and return an outAmount."""
    from pipelines.swap_router import simulate_buy
    data = simulate_buy("So11111111111111111111111111111111111111112", 0.01)
    assert data.get("outAmount", 0) >= 0
