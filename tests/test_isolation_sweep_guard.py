"""Guard the per-file isolation sweep's own logic (#1259).

``scripts/isolation_sweep.py`` is the standing check that each ``tests/test_*.py`` still
passes when run alone. Two things in it can regress unnoticed and are guarded here against a
hermetic temp fixture (not the real suite, so this test stays fast):

* it must **report a file that reds in isolation** as a failure (``any_failed`` True), else
  the sweep would green through a leak — the exact hole #1259 exists to close;
* it must **filter pytest exit-5** ("no tests collected") — a ``test_*.py`` with no
  ``def test_`` is ``empty``, never a failure (the #1244 sweep was tripped by this).

Able to fail: make ``classify_exit`` treat exit-5 as ``fail`` and
``test_empty_file_alone_is_not_a_failure`` reddens; make the sweep swallow a red file and
``test_sweep_reports_a_file_red_in_isolation`` reddens.
"""

import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
_SCRIPT = REPO / "scripts" / "isolation_sweep.py"


def _load_sweep():
    spec = importlib.util.spec_from_file_location("isolation_sweep", _SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sweep = _load_sweep()


# ---- classify_exit: the exit-code → status mapping ------------------------------
def test_classify_exit_pass_empty_fail():
    assert sweep.classify_exit(0) == "pass"
    assert sweep.classify_exit(5) == "empty"  # no tests collected — NOT a failure
    assert sweep.classify_exit(1) == "fail"
    assert sweep.classify_exit(2) == "fail"


# ---- sweep_per_file against crafted files ---------------------------------------
def _write(dir_: Path, name: str, body: str) -> Path:
    path = dir_ / name
    path.write_text(body, encoding="utf-8")
    return path


def test_sweep_reports_a_file_red_in_isolation(tmp_path):
    """A file that reds alone is classified ``fail`` and sets ``any_failed``."""
    _write(tmp_path, "test_clean_ok.py", "def test_ok():\n    assert True\n")
    _write(tmp_path, "test_red_alone.py", "def test_bad():\n    assert False\n")

    results, any_failed = sweep.sweep_per_file(tmp_path)
    status = {path.name: st for path, st, _code in results}

    assert any_failed is True
    assert status["test_clean_ok.py"] == "pass"
    assert status["test_red_alone.py"] == "fail"


def test_empty_file_alone_is_not_a_failure(tmp_path):
    """A test_*.py with no ``def test_`` exits 5 → ``empty``, never ``fail`` (exit-5 filter)."""
    _write(tmp_path, "test_no_tests_here.py", "# no def test_ in this file\nX = 1\n")

    results, any_failed = sweep.sweep_per_file(tmp_path)
    status = {path.name: st for path, st, _code in results}

    assert any_failed is False
    assert status["test_no_tests_here.py"] == "empty"


def test_iter_test_files_matches_pattern(tmp_path):
    """Only ``test_*.py`` files are swept, in sorted order."""
    _write(tmp_path, "test_b.py", "def test_x():\n    pass\n")
    _write(tmp_path, "test_a.py", "def test_x():\n    pass\n")
    _write(tmp_path, "helper.py", "X = 1\n")  # not a test_ file — excluded

    found = [p.name for p in sweep.iter_test_files(tmp_path)]
    assert found == ["test_a.py", "test_b.py"]
