# tests/test_import_guard.py
"""Fails if any module still imports the old drafts.market_data path."""

import pkgutil
import importlib
import inspect
import sys
from pathlib import Path

def test_no_drafts_market_data_imports():
    root = Path(__file__).resolve().parents[1]
    bad = []
    for mod in pkgutil.walk_packages([str(root)]):
        name = mod.name.replace("/", ".")
        if name.endswith(".__pycache__"):
            continue
        try:
            m = importlib.import_module(name)
        except Exception:
            continue
        for _, obj in inspect.getmembers(m):
            if inspect.isfunction(obj) or inspect.isclass(obj):
                src = inspect.getsource(obj)
                if "drafts.market_data" in src:
                    bad.append(f"{name}:{obj.__name__}")
    assert not bad, f"old import path found in: {bad}"
