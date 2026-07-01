"""#339 — the rules core is Sprite-free + display-free (ADR-0004 boundary guard).

The core may use pygame ONLY for `Vector2`/`Rect` value types (deterministic,
headless). It must not touch the pygame *framework* — `sprite`, `Surface`,
`display`, `event`, `draw`, `font`, `image`, `transform`, `mixer`, etc. This is an
able-to-fail AST guard: any `pygame.<attr>` outside the allow-list (or a
`import pygame.<attr>` / `from pygame import <attr>` of one) in a guarded module
reds the test. See ADR-0004.

`core/input.py` is intentionally NOT guarded yet — its `poll()` still imports
`pygame.event`; it joins the set once #342 splits `poll()` out (decision #9).
"""
import ast
import pathlib

import pycats

_ROOT = pathlib.Path(pycats.__file__).resolve().parent

# Only these pygame names are sanctioned in the core (value types) — ADR-0004.
_ALLOWED = {"Vector2", "Rect", "math"}


def _guarded_files() -> list[pathlib.Path]:
    files: list[pathlib.Path] = []
    for pkg in ("combat", "statecharts", "systems", "characters"):
        d = _ROOT / pkg
        if d.is_dir():
            files += sorted(d.rglob("*.py"))
    files += [
        _ROOT / "sim" / "controllers.py",
        _ROOT / "config.py",
        _ROOT / "stats_print.py",
        _ROOT / "core" / "physics.py",
        _ROOT / "entities" / "fighter.py",
    ]
    return [f for f in files if f.exists() and "__pycache__" not in f.parts]


def _framework_refs(path: pathlib.Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    rel = path.relative_to(_ROOT.parent)
    aliases: set[str] = set()
    bad: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                parts = a.name.split(".")
                if parts[0] == "pygame":
                    aliases.add(a.asname or a.name)
                    if len(parts) > 1 and parts[1] not in _ALLOWED:
                        bad.append(f"{rel}:{node.lineno} import {a.name}")
        elif isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] == "pygame":
            parts = node.module.split(".")
            if len(parts) > 1 and parts[1] not in _ALLOWED:
                bad.append(f"{rel}:{node.lineno} from {node.module} import ...")
            for a in node.names:
                if a.name not in _ALLOWED:
                    bad.append(f"{rel}:{node.lineno} from {node.module} import {a.name}")

    for node in ast.walk(tree):
        if (isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Name)
                and node.value.id in aliases
                and node.attr not in _ALLOWED):
            bad.append(f"{rel}:{node.lineno} {node.value.id}.{node.attr}")
    return bad


def test_rules_core_uses_no_pygame_framework():
    offenders: list[str] = []
    for f in _guarded_files():
        offenders += _framework_refs(f)
    assert offenders == [], (
        "rules-core modules touch the pygame framework (ADR-0004: only Vector2/Rect "
        "value types allowed):\n  " + "\n  ".join(offenders)
    )
