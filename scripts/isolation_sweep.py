"""Per-file test-isolation guard: run each tests/test_*.py alone in its own process (#1259).

A test that only passes because a *neighbor* in the same process set up global state
(an initialized ``pygame.font``, a warm render cache, an env var written at import) is an
isolation false-green: green in the full suite, red the moment it runs alone. The #1244
audit found exactly one (``test_main_menu_title.py``) and only because someone ran a manual
per-file sweep — nothing in the suite or CI runs that sweep, so the next such leak would go
unnoticed until another hand audit.

This is that sweep, made standing and runnable on demand (``make test-isolated``). Each
``tests/test_*.py`` is executed in a fresh ``python -m pytest`` process; a file that reddens
alone is reported as an isolation failure and the sweep exits non-zero.

**pytest exit-5 is filtered.** A ``test_*.py`` with zero ``def test_`` collects nothing and
pytest exits 5 ("no tests collected") — that is NOT an isolation failure. The #1244 sweep was
tripped by this (the orphan ``test_air_dodge_shield_physics.py``; its removal is routed
through #1237), so exit-5 is classified as ``empty`` and never counts as a failure.

**Shuffle mode** (``--shuffle``, ``make test-shuffle``): run the *whole* suite together under
``pytest-randomly`` for one or more seeds, catching inter-test *order*-dependence rather than
single-file isolation. This dimension needs ``pytest-randomly`` (added by #1258); the per-file
loop above is dependency-free and runs without it.

Importing this module has no side effects (test_scripts_import.py execs every script) — all
work sits behind ``main()`` and the helper functions.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

# pytest's documented exit codes we care about.
_EXIT_OK = 0  # all collected tests passed
_EXIT_NO_TESTS = 5  # nothing collected — an empty test_*.py, NOT an isolation failure

# Default seeds for --shuffle. Fixed (not random) so a red shuffle is reproducible and
# the run is deterministic across invocations.
_DEFAULT_SEEDS = (0, 1259)


def iter_test_files(tests_dir: Path, pattern: str = "test_*.py") -> list[Path]:
    """Every test file under ``tests_dir`` matching ``pattern``, sorted."""
    return sorted(tests_dir.glob(pattern))


def classify_exit(code: int) -> str:
    """Map a per-file pytest exit code to ``pass`` / ``empty`` / ``fail``.

    ``empty`` (exit 5, no tests collected) is deliberately distinct from ``fail`` — a
    ``test_*.py`` with no ``def test_`` is not an isolation leak.
    """
    if code == _EXIT_OK:
        return "pass"
    if code == _EXIT_NO_TESTS:
        return "empty"
    return "fail"


def run_file(test_file: Path) -> int:
    """Run one test file alone in a fresh pytest process; return its exit code.

    Uses ``sys.executable`` so the child runs under the same interpreter/venv as the
    sweep. The default plugin set is left intact — in particular ``pytest-randomly`` stays
    active, so a test that asserts on its own plugin environment (e.g.
    ``test_dev_deps_test_tooling``) behaves the same alone as in the suite. This sweep checks
    cross-*file* isolation (each file in its own process); intra-file order is the
    ``--shuffle`` mode's concern, so there is nothing to gain by forcing ``-p no:randomly``
    here — and doing so would falsely redden a plugin-environment assertion.
    """
    args = [sys.executable, "-m", "pytest", "-q", str(test_file)]
    return subprocess.run(args, check=False).returncode


def sweep_per_file(tests_dir: Path, pattern: str = "test_*.py") -> tuple[list[tuple[Path, str, int]], bool]:
    """Run every matching test file alone; return ``(results, any_failed)``.

    ``results`` is ``(path, status, exit_code)`` per file, in sweep order. ``any_failed``
    is True iff at least one file classified as ``fail`` (``empty`` never counts).
    """
    results: list[tuple[Path, str, int]] = []
    any_failed = False
    for test_file in iter_test_files(tests_dir, pattern):
        code = run_file(test_file)
        status = classify_exit(code)
        if status == "fail":
            any_failed = True
        results.append((test_file, status, code))
    return results, any_failed


def run_shuffled_suite(tests_dir: Path, seed: int) -> int:
    """Run the whole suite together under a fixed pytest-randomly seed; return exit code."""
    args = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "-p",
        "randomly",
        f"--randomly-seed={seed}",
        str(tests_dir),
    ]
    return subprocess.run(args, check=False).returncode


def _run_per_file(tests_dir: Path, pattern: str) -> int:
    results, any_failed = sweep_per_file(tests_dir, pattern)
    passed = [r for r in results if r[1] == "pass"]
    empty = [r for r in results if r[1] == "empty"]
    failed = [r for r in results if r[1] == "fail"]
    print(
        f"\nper-file isolation sweep: {len(results)} files "
        f"({len(passed)} pass, {len(empty)} empty/skipped, {len(failed)} FAIL)"
    )
    for path, _status, code in failed:
        print(f"  FAIL (exit {code}, red in isolation): {path}")
    if any_failed:
        print(
            "\nisolation FAILURE — the files above pass in the full suite but red alone. "
            "Each is a test depending on global state a neighbor set up; fix per file "
            "(see #1259 / the render_isolation precedent in tests/conftest.py)."
        )
        return 1
    print("all files pass in isolation.")
    return 0


def _run_shuffle(tests_dir: Path, seeds: list[int]) -> int:
    any_failed = False
    for seed in seeds:
        print(f"\n--- shuffle-order run, seed {seed} ---")
        code = run_shuffled_suite(tests_dir, seed)
        if code != _EXIT_OK:
            any_failed = True
            print(f"  shuffle seed {seed}: pytest exit {code} — order-dependence surfaced")
    if any_failed:
        print(
            "\nshuffle-order FAILURE — the suite reddened under a randomized order. This is "
            "inter-test order-dependence; find the polluting pair and isolate it."
        )
        return 1
    print(f"\nsuite green under all {len(seeds)} shuffle seed(s).")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--tests-dir",
        default=str(Path(__file__).resolve().parents[1] / "tests"),
        help="directory of test_*.py files to sweep (default: repo tests/)",
    )
    parser.add_argument("--pattern", default="test_*.py", help="glob for test files (default: test_*.py)")
    parser.add_argument(
        "--shuffle",
        action="store_true",
        help="run the whole suite under pytest-randomly seeds instead of the per-file sweep",
    )
    parser.add_argument(
        "--seed",
        type=int,
        action="append",
        dest="seeds",
        help="a pytest-randomly seed for --shuffle (repeatable; default: 0 and 1259)",
    )
    args = parser.parse_args(argv)
    tests_dir = Path(args.tests_dir)

    if args.shuffle:
        seeds = args.seeds if args.seeds else list(_DEFAULT_SEEDS)
        return _run_shuffle(tests_dir, seeds)
    return _run_per_file(tests_dir, args.pattern)


if __name__ == "__main__":
    raise SystemExit(main())
