"""
Fail if *repo code* still imports drafts.market_data.
Gracefully skip binary/ext modules with no source.
"""
import pkgutil, importlib, inspect, pathlib, re, types

root = pathlib.Path(__file__).resolve().parents[1]
bad = []

for mod in pkgutil.walk_packages([str(root)]):
    name = mod.name
    # skip internal pycache + test packages
    if name.endswith(".__pycache__") or name.startswith("tests."):
        continue
    try:
        m = importlib.import_module(name)
        # compiled wheels (torch, pyarrow, etc.) have no source
        if not isinstance(m, types.ModuleType) or not hasattr(m, "__file__"):
            continue
        src_path = pathlib.Path(m.__file__ or "")
        if src_path.suffix in {".pyd", ".so"}:  # binary module
            continue
        src = inspect.getsource(m)
    except (OSError, TypeError):
        # no source available – ignore
        continue
    if re.search(r"drafts\.market_data", src):
        bad.append(name)

assert not bad, f"outdated import detected in {bad}"
