"""Print the SCRIPTS section of `make help` — derived, so it never drifts (#1140).

Scans the repo's runnable entry points (root ``*.py`` + ``scripts/*.py`` / ``*.sh``)
and prints each with its one-line purpose, read straight from the file:

- ``.py`` → the first line of the module docstring (via ``ast``, so nothing is
  imported or executed — reading a script never runs it).
- ``.sh`` → the first ``#`` comment line after any shebang.

A newly-added script appears here automatically; there is no hand-maintained list to
keep in sync. ``make help`` calls this to render its SCRIPTS block; the make-targets
and sim sections above it stay hand-listed in the Makefile (#1127-style split ruling:
derive scripts, hand-list make/sim).
"""

from __future__ import annotations

import ast
from pathlib import Path

# Files that live in the scanned dirs but are not runnable entry points.
EXCLUDE_ROOT = {"conftest.py"}
EXCLUDE_SCRIPTS = {"help_scripts.py", "__init__.py"}

_NO_DESC = "(no description — add a module docstring)"


def repo_root() -> Path:
    """The repo root — the parent of this file's ``scripts/`` directory."""
    return Path(__file__).resolve().parent.parent


def _py_docline(path: Path) -> str:
    """First line of ``path``'s module docstring, or a placeholder. No import/exec."""
    try:
        doc = ast.get_docstring(ast.parse(path.read_text(encoding="utf-8")))
    except (OSError, SyntaxError, ValueError):
        return _NO_DESC
    if not doc:
        return _NO_DESC
    return doc.splitlines()[0].strip()


def _sh_docline(path: Path) -> str:
    """First ``#`` comment line after any shebang in a shell script, or placeholder."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return _NO_DESC
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#!") or not stripped:
            continue
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()
        break  # first non-comment, non-blank line — no leading comment block
    return _NO_DESC


def _docline(path: Path) -> str:
    return _sh_docline(path) if path.suffix == ".sh" else _py_docline(path)


def collect() -> list[tuple[str, str]]:
    """Return ``(display_path, description)`` for every runnable entry point, sorted.

    Root ``*.py`` first (sorted), then ``scripts/`` ``*.py`` + ``*.sh`` (sorted),
    each display path relative to the repo root.
    """
    root = repo_root()
    entries: list[tuple[str, str]] = []

    for path in sorted(root.glob("*.py")):
        if path.name in EXCLUDE_ROOT:
            continue
        entries.append((path.name, _docline(path)))

    scripts_dir = root / "scripts"
    for path in sorted(scripts_dir.glob("*.py")) + sorted(scripts_dir.glob("*.sh")):
        if path.name in EXCLUDE_SCRIPTS:
            continue
        entries.append((f"scripts/{path.name}", _docline(path)))

    return entries


def render() -> str:
    """The SCRIPTS block as printed under ``make help``."""
    entries = collect()
    width = max((len(name) for name, _ in entries), default=0)
    lines = ["SCRIPTS (run: python <path>):"]
    for name, desc in entries:
        lines.append(f"  {name:<{width}}  {desc}")
    return "\n".join(lines)


def main() -> None:
    print(render())


if __name__ == "__main__":
    main()
