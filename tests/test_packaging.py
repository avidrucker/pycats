"""
Tests for the repo-root pyproject.toml packaging contract (#885).

pycats is imported as `python -m pycats.game` from the repo root; before #885
there was no build metadata, so `pip install -e .` was impossible and the
separate pycats-editor repo (#882) could not couple to it via an editable
install. These tests assert the minimal packaging contract that makes pycats
editable-installable, and pin the declared runtime dependencies to
requirements.txt (the canonical runtime install) so the two cannot drift.

They read pyproject.toml as data (tomllib, stdlib) — no build/install step, no
network — so they run fast and deterministically in the normal suite. The proof
that an editable install actually works (`pip install -e .` then `import pycats`
from a neutral cwd) is the ticket's manual acceptance check, recorded on #885.
"""

from pathlib import Path

import tomllib

REPO_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = REPO_ROOT / "pyproject.toml"
REQUIREMENTS = REPO_ROOT / "requirements.txt"


def _load_pyproject():
    with PYPROJECT.open("rb") as fh:
        return tomllib.load(fh)


def _requirements_runtime_deps():
    """Non-comment, non-blank lines from requirements.txt — the runtime SSOT."""
    deps = []
    for raw in REQUIREMENTS.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        deps.append(line)
    return deps


def test_pyproject_exists():
    assert PYPROJECT.is_file(), f"expected packaging metadata at {PYPROJECT}"


def test_build_system_is_setuptools():
    build = _load_pyproject()["build-system"]
    assert build["build-backend"] == "setuptools.build_meta"
    assert any("setuptools" in req for req in build["requires"])


def test_project_name_and_python_floor():
    project = _load_pyproject()["project"]
    assert project["name"] == "pycats"
    assert ">=3.12" in project["requires-python"]


def test_dependencies_mirror_requirements_txt():
    """pyproject runtime deps must exactly mirror requirements.txt (no drift)."""
    declared = set(_load_pyproject()["project"]["dependencies"])
    canonical = set(_requirements_runtime_deps())
    assert declared == canonical, (
        "pyproject [project].dependencies must mirror requirements.txt "
        f"(the runtime SSOT).\n  pyproject: {sorted(declared)}\n  "
        f"requirements.txt: {sorted(canonical)}"
    )


def test_package_discovery_scoped_to_pycats():
    """Discovery is scoped to the pycats package so tests/docs/scripts aren't packaged."""
    find = _load_pyproject()["tool"]["setuptools"]["packages"]["find"]
    include = find["include"]
    assert "pycats*" in include
    assert all(pattern.startswith("pycats") for pattern in include), (
        f"every discovery include must be pycats-scoped, got {include}"
    )
