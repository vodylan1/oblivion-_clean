"""Import‑guard – ensure no stale `drafts.market_data` references remain."""
import importlib
import inspect
import pkgutil
import pathlib
import re
import types

root = pathlib.Path(__file__).resolve().parents[1]
bad: list[str] = []

for mod in pkgutil.walk_packages([str(root)]):
    name = mod.name
    try:
        m = importlib.import_module(name)
    except Exception:
        continue

    # Skip namespace / built‑in stubs with no __file__
    if not hasattr(m, "__file__"):
        continue
    if m.__file__ is None:
        continue
    if not m.__file__.startswith(str(root)):
        continue  # external libs

    src = inspect.getsource(m)
    if re.search(r"drafts\.market_data", src):
        bad.append(name)

assert not bad, f"outdated import detected in {bad}"
