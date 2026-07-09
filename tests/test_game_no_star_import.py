"""game.py + app.py import-safety + lint-visibility guards (#490 → #701 → #707).

Two layers, now covering both the entry point and the shell object:

1. **Import-safety (#701, extended to app.py in #707).** `pycats.game` wraps its whole
   runtime — pygame.init, settings I/O, the drive loop — in `main()` behind an `if __name__`
   guard, and the per-frame body + collaborators live on `App` in `pycats.app`. **Importing
   either module has no observable side effects** (game.py used to run the loop and
   `sys.exit()` at import — the #386-class untestable-loop blindspot). The monitored-import
   tests patch `pygame.init` / `pygame.display.set_mode` / `settings.load`, import the
   module, and assert none fired. Able-to-fail: move any setup back to module scope (or
   construct an `App` at import) and the import re-triggers it → red.

2. **Lint visibility (#490, slice 2 of #486).** Neither module may `import *` — `from
   .config import *` made pyflakes report "unable to detect undefined names" and skip the
   untested module. These are source-level (AST over the file text); they don't import.
"""

import ast
import importlib
import pathlib
import sys

import pygame  # type: ignore
import pytest

import pycats.config as config
import pycats.settings as settings

_PYCATS = pathlib.Path(__file__).resolve().parent.parent / "pycats"
_MODULE_FILES = {"game": _PYCATS / "game.py", "app": _PYCATS / "app.py"}


def _tree(module):
    return ast.parse(_MODULE_FILES[module].read_text())


# --- layer 1: import-safety (#701 / #707) --------------------------------------


def _assert_import_is_inert(module_name, monkeypatch):
    calls = []
    monkeypatch.setattr(pygame, "init", lambda *a, **k: calls.append("pygame.init"))
    monkeypatch.setattr(
        pygame.display,
        "set_mode",
        lambda *a, **k: (calls.append("set_mode"), pygame.Surface((1, 1)))[1],
    )
    monkeypatch.setattr(settings, "load", lambda *a, **k: (calls.append("settings.load"), {})[1])

    # Force the module body to re-execute under the monitors even if a prior test imported
    # it, so the assertion reflects *this* import's side effects.
    sys.modules.pop(module_name, None)
    mod = importlib.import_module(module_name)
    assert calls == [], f"import {module_name} triggered runtime side effects: {calls}"
    return mod


def test_importing_game_has_no_side_effects(monkeypatch):
    """import pycats.game must not init pygame, open a window, read settings, or run the
    loop — the whole runtime lives behind `if __name__ == "__main__": main()`."""
    game = _assert_import_is_inert("pycats.game", monkeypatch)
    assert callable(game.main), "pycats.game must expose a callable main() entry point"


def test_importing_app_has_no_side_effects(monkeypatch):
    """import pycats.app must be inert too — the collaborators/window are built only when an
    `App` is constructed (inside main()), never at import (#707)."""
    app_mod = _assert_import_is_inert("pycats.app", monkeypatch)
    assert isinstance(app_mod.App, type), "pycats.app must expose the App class"


def test_game_defines_main_entry_point():
    # Source-level guard (no import): the runtime is wrapped in a `def main()` called from
    # an `if __name__ == "__main__"` guard — the structural shape import-safety depends on.
    tree = _tree("game")
    has_main = any(isinstance(n, ast.FunctionDef) and n.name == "main" for n in ast.walk(tree))
    assert has_main, "game.py must define a `main()` function holding the runtime"
    guards = [
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.If)
        and isinstance(n.test, ast.Compare)
        and isinstance(n.test.left, ast.Name)
        and n.test.left.id == "__name__"
    ]
    assert guards, 'game.py must guard the run with `if __name__ == "__main__":`'


# --- layer 2: lint visibility (#490) -------------------------------------------


@pytest.mark.parametrize("module", ["game", "app"])
def test_module_has_no_star_import(module):
    stars = [
        node
        for node in ast.walk(_tree(module))
        if isinstance(node, ast.ImportFrom) and any(alias.name == "*" for alias in node.names)
    ]
    assert not stars, f"{module}.py must not use `import *` (it blinds pyflakes on the untested module)"


@pytest.mark.parametrize("module", ["game", "app"])
def test_module_config_imports_all_resolve(module):
    # every name the module imports from .config must exist in config (guards typo/rename).
    # Not every module imports from config (game.py no longer does since #707) — this only
    # checks the ones present; the no-star guard above catches a regression to `import *`.
    imported = [
        alias.name
        for node in ast.walk(_tree(module))
        if isinstance(node, ast.ImportFrom) and node.module == "config" and node.level == 1
        for alias in node.names
    ]
    missing = [n for n in imported if not hasattr(config, n)]
    assert not missing, f"{module}.py imports names absent from config: {missing}"
