from drafts.weighting_algo import update_weights


def test_weight_bounds():
    w = update_weights({"good": [0.5] * 50, "bad": [-0.5] * 50, "new": []})
    assert w["good"] == 2.0
    assert w["bad"] == 0.0
    assert w["new"] == 1.0
