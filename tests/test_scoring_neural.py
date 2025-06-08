"""
tests/test_scoring_neural.py
Verifies that the neural scorer obeys the weight file and clamps 0-100.
"""

# --------------------------------------------------------------------------- #
def test_neural_score_range():
    """Score is always in [0, 100]."""
    from core.scoring_engine.neural_score import compute_score

    s = compute_score({"sol_price": 0, "meme_hype": 150})
    assert 0.0 <= s <= 100.0


def test_neural_weight_bias(tmp_path, monkeypatch):
    """
    Point the scorer at a temp weight file with +99 bias.
    Expect exactly 99 regardless of inputs.
    """
    bias_cfg = tmp_path / "weights.json"
    bias_cfg.write_text('{"w_price": 0, "w_meme": 0, "bias": 99}')

    from core.scoring_engine import neural_score as ns

    # Redirect config + clear cached weights ― NO reload required
    monkeypatch.setattr(ns, "_CFG_PATH", bias_cfg)
    monkeypatch.setattr(ns, "_WEIGHTS", None)

    assert ns.compute_score({"sol_price": 200, "meme_hype": 0}) == 99.0
