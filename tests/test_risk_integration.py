from decimal import Decimal
import importlib
from pipelines.risk_manager import position_limit_usd as pipe_limit


def test_manager_delegates_to_pipeline(monkeypatch):
    # monkey-patch the pipeline func to prove delegation works
    monkeypatch.setattr(
        "pipelines.risk_manager.position_limit_usd",
        lambda: Decimal("42"),
        raising=True,
    )

    from core.risk_manager import manager as rm  # import after patch

    importlib.reload(rm)  # bind the new lambda

    assert rm.position_limit_usd() == Decimal("42")
