# tests/test_make_help_targets.py
"""Guard: the `goldens` target stays discoverable via `make help` (#783).

The Makefile is the command SSOT (#724). `PYCATS_UPDATE_GOLDENS=1` is the only
way to regenerate the file-based goldens, and `make goldens` is the discoverable
wrapper for it. This test reds if the `make help` row drifts off or the target
is deleted — the two ways the wrapper could stop being findable.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
MAKEFILE = REPO_ROOT / "Makefile"

# `make` is not a declared test dependency; skip cleanly where it is absent
# rather than red on an environment issue.
pytestmark = pytest.mark.skipif(
    shutil.which("make") is None or not MAKEFILE.exists(),
    reason="GNU make (or the Makefile) is unavailable in this environment",
)


def _make(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["make", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def test_make_help_lists_goldens() -> None:
    """`make help` prints the `make goldens` row (discoverability guard)."""
    result = _make("help")
    assert result.returncode == 0, result.stderr
    assert "make goldens" in result.stdout, (
        "the `make goldens` row is missing from `make help` — regen is no longer "
        f"discoverable via the command SSOT.\nhelp output:\n{result.stdout}"
    )


def test_goldens_target_is_defined() -> None:
    """The `goldens` target exists (a help row without a target would still fail here)."""
    # -n dry-runs the recipe without executing pytest; returns non-zero if the
    # target is undefined ("No rule to make target 'goldens'").
    result = _make("-n", "goldens")
    assert result.returncode == 0, (
        f"`make -n goldens` failed — the target is undefined despite the help row.\nstderr:\n{result.stderr}"
    )
    assert "PYCATS_UPDATE_GOLDENS=1" in result.stdout, (
        "the `goldens` recipe no longer sets PYCATS_UPDATE_GOLDENS=1 — it would "
        f"not regenerate anything.\nrecipe:\n{result.stdout}"
    )
