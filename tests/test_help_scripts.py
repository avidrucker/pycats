"""Guard the derived SCRIPTS help printer (`scripts/help_scripts.py`, #1140).

The printer feeds `make help`'s SCRIPTS block by reading each script's one-line
purpose from disk, so a new script self-documents. These tests pin that behavior:
every known entry point is listed with a real description, non-entry files
(conftest.py, the printer itself) are excluded, and the derivation reads docstrings
without importing the scripts.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_HELP = _REPO_ROOT / "scripts" / "help_scripts.py"


def _load():
    spec = importlib.util.spec_from_file_location("help_scripts", _HELP)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_lists_known_entry_points_with_descriptions():
    entries = dict(_load().collect())
    for name in ("watch.py", "bench.py", "parity_report.py", "scripts/run_cmd.py"):
        assert name in entries, f"{name} missing from SCRIPTS help"
        desc = entries[name]
        assert desc and not desc.startswith("(no description"), f"{name} listed without a real description: {desc!r}"


def test_excludes_non_entry_points():
    names = {name for name, _ in _load().collect()}
    # conftest.py is pytest config, not a runnable script; the printer must not
    # list itself either.
    assert "conftest.py" not in names
    assert "scripts/help_scripts.py" not in names


def test_covers_every_scripts_py_on_disk():
    """Drift-guard: every scripts/*.py on disk (bar the exclude list) is listed —
    so adding a script without a docstring can't drop it from help unnoticed."""
    mod = _load()
    listed = {name for name, _ in mod.collect() if name.endswith(".py") and name.startswith("scripts/")}
    on_disk = {f"scripts/{p.name}" for p in (_REPO_ROOT / "scripts").glob("*.py") if p.name not in mod.EXCLUDE_SCRIPTS}
    assert on_disk == listed


def test_render_has_grouped_header():
    out = _load().render()
    assert out.startswith("SCRIPTS (run: python <path>):")
    assert "watch.py" in out
