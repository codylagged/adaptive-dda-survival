"""The window can start without pulling in pandas or matplotlib."""

import importlib
import sys


def test_frontend_imports_without_pandas():
    for name in list(sys.modules):
        if name.startswith("pandas") or name.startswith("matplotlib"):
            del sys.modules[name]
    importlib.import_module("frontend.app")
    assert "pandas" not in sys.modules
    assert "matplotlib" not in sys.modules
