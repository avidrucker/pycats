"""game.py import-safety + lint-visibility guards (#490 → flipped in #701, C2 of #280).

Two layers here:

1. **Import-safety (#701).** `pycats.game` now wraps its whole runtime — pygame.init, the
   window, settings I/O, and the game loop — in `main()` behind an `if __name__` guard, so
   **importing the module has no observable side effects** (it used to run the loop and
   `sys.exit()` at import, which is the #386-class untestable-loop blindspot). The
   monitored-import test below asserts that: it patches `pygame.init` /
   `pygame.display.set_mode` / `settings.load`, imports `pycats.game`, and asserts none
   fired. Able-to-fail: move any of that setup back to module scope (or drop the
   `if __name__` guard) and the import re-triggers it → red. (Before #701 this file could
   not import game.py at all — the module-level loop blocked forever — hence the AST-only
   checks in layer 2.)

2. **Lint visibility (#490, slice 2 of #486).** game.py must stay `import *`-free so
   pyflakes can lint it. `from .config import *` made pyflakes report "unable to detect
   undefined names" and skip the one module with no runtime coverage. These are source-
   level (AST over the file text); they don't need to import the module.
"""

import ast
import importlib
import pathlib
import sys

import pygame  # type: ignore

import pycats.config as config
import pycats.settings as settings

_GAME = pathlib.Path(__file__).resolve().parent.parent / "pycats" / "game.py"


def _game_tree():
    return ast.parse(_GAME.read_text())


# --- layer 1: import-safety (#701) ---------------------------------------------


def test_importing_game_has_no_side_effects(monkeypatch):
    """import pycats.game must not init pygame, open a window, read settings, or run the
    loop — the whole runtime lives behind `if __name__ == "__main__": main()`."""
    calls = []
    monkeypatch.setattr(pygame, "init", lambda *a, **k: calls.append("pygame.init"))
    monkeypatch.setattr(
        pygame.display,
        "set_mode",
        lambda *a, **k: (calls.append("set_mode"), pygame.Surface((1, 1)))[1],
    )
    monkeypatch.setattr(settings, "load", lambda *a, **k: (calls.append("settings.load"), {})[1])

    # Force the module body to re-execute under the monitors even if a prior test
    # imported it, so the assertion reflects *this* import's side effects.
    sys.modules.pop("pycats.game", None)
    game = importlib.import_module("pycats.game")

    assert calls == [], f"import pycats.game triggered runtime side effects: {calls}"
    assert callable(game.main), "pycats.game must expose a callable main() entry point"


def test_game_defines_main_entry_point():
    # Source-level guard (no import): the runtime is wrapped in a `def main()` called from
    # an `if __name__ == "__main__"` guard — the structural shape import-safety depends on.
    tree = _game_tree()
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


def test_game_has_no_star_import():
    stars = [
        node
        for node in ast.walk(_game_tree())
        if isinstance(node, ast.ImportFrom) and any(alias.name == "*" for alias in node.names)
    ]
    assert not stars, "game.py must not use `import *` (it blinds pyflakes on the untested module)"


def test_game_config_imports_all_resolve():
    # every name game.py imports from .config must exist in config (guards typo/rename)
    imported = [
        alias.name
        for node in ast.walk(_game_tree())
        if isinstance(node, ast.ImportFrom) and node.module == "config" and node.level == 1
        for alias in node.names
    ]
    assert imported, "expected an explicit `from .config import (...)` in game.py"
    missing = [n for n in imported if not hasattr(config, n)]
    assert not missing, f"game.py imports names absent from config: {missing}"
