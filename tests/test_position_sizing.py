# tests/test_position_sizing.py
"""
Verifies position sizing ≈ risk_pct × balance
(using monkey-patched balance helper to avoid RPC calls).
"""

def test_position_size(monkeypatch):
    from pipelines import execution_engine as ee

    # force parameters
    monkeypatch.setattr(ee, "RISK_PCT", 0.05)  # 5 %
    monkeypatch.setattr(ee, "_balance_lamports", lambda n: int(10 * 1e9))  # 10 SOL

    size_lamp = ee._size_lamports("mainnet")
    assert abs(size_lamp/1e9 - 0.5) < 1e-6   # 0.5 SOL == 5 % of 10 SOL
