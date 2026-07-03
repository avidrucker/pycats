"""#490 (slice 2 of #486) — game.py must stay `import *`-free so pyflakes can lint it.

game.py used `from .config import *`, which made pyflakes report "unable to detect
undefined names" and skip the one module with no test coverage (its loop runs at
import). These guards are source-level (AST over the file text) — they deliberately do
NOT import game.py, whose top-level loop would run on import. Able-to-fail: with the
star-import present, test_game_has_no_star_import is red.
"""
import ast
import pathlib

import pycats.config as config

_GAME = pathlib.Path(__file__).resolve().parent.parent / "pycats" / "game.py"


def _game_tree():
    return ast.parse(_GAME.read_text())


def test_game_has_no_star_import():
    stars = [
        node
        for node in ast.walk(_game_tree())
        if isinstance(node, ast.ImportFrom)
        and any(alias.name == "*" for alias in node.names)
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
