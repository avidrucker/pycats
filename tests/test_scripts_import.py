"""#1112: smoke-import guard against script rot (#1109 findings).

Scripts outside `pycats/` and `tests/` are not imported by the suite unless a
specific test names them, so a package refactor can break one while every test
stays green — exactly what happened to `scripts/profile_frame_budget.py` at the
`pycats/shell/` + `pycats/storage/` reorg (the #1091 finding).

This guard imports every such script by path under `SDL_VIDEODRIVER=dummy`, one
test node per script (auto-discovered — a new script under `scripts/` is covered
with no edit here). It asserts nothing about behavior; behavior/output is guarded
where it matters by test_benchmark / test_watch_* / test_parity_status_report /
test_run_cmd / test_hitbox_label_migration. This is only the import floor.

Able-to-fail: reverting the import repair in `scripts/profile_frame_budget.py`
turns its node red (`ImportError: cannot import name 'runtime_settings'`).

Invariant relied on: no script opens a window at import time — every `set_mode`
sits behind `main()` / `if __name__ == "__main__"`. A future module-top-level
`set_mode` would hang this test under the dummy driver; that is the signal to move
the call into `main()`, not to skip the script here.
"""

import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]

# `scripts/` is a bare glob — anything runnable dropped there is covered.
_SCRIPTS_DIR = sorted((REPO / "scripts").glob("*.py"))

# The repo root also holds `conftest.py` and non-script modules, so root scripts
# are an explicit allowlist rather than a glob.
_ROOT_SCRIPTS = [REPO / name for name in ("bench.py", "bench_render.py", "parity_report.py", "watch.py")]

_SCRIPTS = _SCRIPTS_DIR + _ROOT_SCRIPTS


def _import_by_path(path: Path):
    """Import `path` as an isolated module (not registered in sys.modules) and
    return it. Raises whatever the module's top-level code raises."""
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize("script", _SCRIPTS, ids=lambda p: p.name)
def test_script_imports(script, monkeypatch):
    """Every runnable script outside pycats/ and tests/ imports cleanly under the
    dummy video driver — so a package refactor that breaks a script's imports
    reddens the suite instead of rotting unnoticed (#1112 / #1109)."""
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    _import_by_path(script)


def test_discovery_is_non_empty():
    """Guard the guard: if the globs stop matching, the parametrized test would
    pass vacuously (zero nodes). Assert we actually found the known scripts."""
    names = {p.name for p in _SCRIPTS}
    assert {"profile_frame_budget.py", "bench.py", "watch.py"} <= names
