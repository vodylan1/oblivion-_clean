import torch
from core.scoring_engine.model import ScoringModel


def test_model_forward_shape():
    model = ScoringModel()
    x = torch.randn(10, 32)
    y = model(x)
    assert y.shape == (10, 1)
    assert torch.all((0 <= y) & (y <= 100))
