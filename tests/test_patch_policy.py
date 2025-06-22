import importlib, pathlib, time
from core.patch_core import patch_core as pc


def test_autopatch_blocked_by_sandbox(monkeypatch):
    pathlib.Path("config").mkdir(exist_ok=True)
    pathlib.Path("logs").mkdir(exist_ok=True)

    pathlib.Path("config/patch_policy.yaml").write_text("sandbox_hours: 48")
    ml = pathlib.Path("logs/mutation_log.md")
    ml.write_text("x")
    ml.touch(time.time() - 60)  # 1 min ago

    called = {"ran": False}
    monkeypatch.setattr(
        pc, "_apply_patch", lambda *a, **k: called.__setitem__("ran", True)
    )
    importlib.reload(pc)
    pc.request_autopatch()
    assert called["ran"] is False
