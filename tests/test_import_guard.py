"""Fail if any code still imports drafts.market_data."""
import pkgutil, importlib, inspect, sys, pathlib, re
root = pathlib.Path(__file__).resolve().parents[1]
bad = []
for mod in pkgutil.walk_packages([str(root)]):
    name = mod.name
    if name.endswith(".__pycache__"): continue
    try:
        m = importlib.import_module(name)
    except Exception:
        continue
    src = inspect.getsource(m)
    if re.search(r"drafts\.market_data", src):
        bad.append(name)
assert not bad, f"outdated import detected in {bad}"
