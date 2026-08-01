"""#339 — the rules core is Sprite-free + display-free (ADR-0004 boundary guard).

The core may use pygame ONLY for `Vector2`/`Rect` value types (deterministic,
headless). It must not touch the pygame *framework* — `sprite`, `Surface`,
`display`, `event`, `draw`, `font`, `image`, `transform`, `mixer`, etc. This is an
able-to-fail AST guard: any `pygame.<attr>` outside the allow-list (or a
`import pygame.<attr>` / `from pygame import <attr>` of one) in a guarded module
reds the test. See ADR-0004.

`core/input.py` joined the guarded set in #342 — its `poll()` (which imported
`pygame.event`) moved to `pycats/input_poll.py` (present layer, decision #9), so
the port is now pygame-free.
"""

import ast
import pathlib
import subprocess
import sys
import textwrap

import pycats

_ROOT = pathlib.Path(pycats.__file__).resolve().parent

# Only these pygame names are sanctioned in the core (value types) — ADR-0004.
_ALLOWED = {"Vector2", "Rect", "math"}


def _guarded_files() -> list[pathlib.Path]:
    files: list[pathlib.Path] = []
    # `config` joined this set as a package (#934 split it from a flat module);
    # the guard tracks the package so its submodules stay covered (#968).
    for pkg in ("combat", "statecharts", "systems", "characters", "config"):
        d = _ROOT / pkg
        if d.is_dir():
            files += sorted(d.rglob("*.py"))
    files += [
        _ROOT / "sim" / "controllers.py",
        _ROOT / "stats_print.py",
        _ROOT / "core" / "physics.py",
        _ROOT / "core" / "input.py",
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
        if (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id in aliases
            and node.attr not in _ALLOWED
        ):
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


# #968 — the import-time boundary gate (ADR-0004, epic #833 §6).
#
# The AST guard above proves no *forbidden* pygame name is written in a guarded
# module. This gate proves the stronger property §6 asks for: that every submodule
# of the named rules-core packages IMPORTS with pygame absent from `sys.modules` —
# i.e. the core carries no import-time dependency on the framework at all (not even
# the allowed value-type imports pulling pygame in). It is the executable form of
# the ADR-0004 aspiration, complementing the read-only AST check with a run check.
#
# Scope note: `systems` is NOT yet gated — `systems.status_model` reaches pygame
# transitively (status_model -> runtime_settings -> settings -> display), a
# structural coupling tracked as a follow-up of #833 §6. `combat` is already fully
# import-clean; `core` becomes clean once `core/physics.py` drops its dead
# `import pygame` (annotations are stringized via `from __future__ import
# annotations`, so nothing in the module needs pygame at import time).
_IMPORT_GATE_PACKAGES = ("combat", "core")

_IMPORT_GATE_SCRIPT = textwrap.dedent(
    """
    import importlib, pkgutil, sys

    class _BlockPygame:
        # Refuse to import pygame or any submodule of it.
        def find_spec(self, name, path=None, target=None):
            if name == "pygame" or name.startswith("pygame."):
                raise ImportError("pygame is absent (import-time boundary gate): " + name)
            return None

    sys.meta_path.insert(0, _BlockPygame())

    import pycats  # must itself be pygame-free

    fails = []

    def _onerror(name):
        fails.append(name + ": failed while walking (package import error)")

    for pkgname in {packages!r}:
        pkg = importlib.import_module("pycats." + pkgname)
        for info in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + ".", onerror=_onerror):
            try:
                importlib.import_module(info.name)
            except Exception as exc:
                fails.append(info.name + ": " + type(exc).__name__ + ": " + str(exc))

    if fails:
        print("\\n".join(fails))
        sys.exit(1)
    sys.exit(0)
    """
)


def test_rules_core_imports_without_pygame_framework():
    """Every submodule of `combat`/`core` imports with pygame absent from sys.modules.

    Runs in a subprocess so the pygame-blocking meta-path finder and the fresh
    imports never touch the pytest session's own `sys.modules` (ADR-0004, #833 §6).
    Able-to-fail: adding a top-level `import pygame` to any guarded submodule (or
    reverting `core/physics.py`'s dead-import removal) makes the subprocess exit 1.
    """
    script = _IMPORT_GATE_SCRIPT.format(packages=_IMPORT_GATE_PACKAGES)
    proc = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        cwd=str(_ROOT.parent),
    )
    assert proc.returncode == 0, (
        "rules-core submodules require pygame at import time (ADR-0004 import-time "
        "gate — only value-type USE is allowed, never an import-time dependency):\n" + proc.stdout + proc.stderr
    )
