"""Dev test-tooling contract: pytest-cov + pytest-randomly present, hypothesis absent (#1258).

The #1242 audit needs coverage/branch numbers (`pytest-cov`) and a default-seed suite
shuffle to catch order-dependent isolation false-greens (`pytest-randomly`). Both were
approved for exactly this repo in the #1246 D3 ruling; `hypothesis` was deferred there until
a property-test ticket needs it.

These assertions are able to fail: before the #1258 install both plugins raise
``ModuleNotFoundError`` on import and are unregistered with pytest, so every check here
reddens; after the install they pass. The `hypothesis`-absent check guards the deferral —
it reddens if `hypothesis` is ever added without its own approving ticket.

Read as data (no install step, no network): the manifest lines from requirements-dev.txt,
the importability of the two modules, their registration with the running pytest, and the
absence of `hypothesis`.
"""

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS_DEV = REPO_ROOT / "requirements-dev.txt"


def _requirements_dev_deps():
    """Non-comment, non-blank lines from requirements-dev.txt (the dev-tooling list)."""
    deps = []
    for raw in REQUIREMENTS_DEV.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        deps.append(line)
    return deps


def test_requirements_dev_declares_the_two_plugins():
    """Both dev deps are declared in the manifest (#1246 D3 / #1258)."""
    declared = set(_requirements_dev_deps())
    for pkg in ("pytest-cov", "pytest-randomly"):
        assert pkg in declared, (
            f"{pkg} must be declared in requirements-dev.txt (approved in #1246 D3, "
            f"added by #1258); got {sorted(declared)}"
        )


def test_pytest_cov_and_randomly_are_importable():
    """Both plugins resolve in the dev .venv — red before the #1258 install."""
    for module in ("pytest_cov", "pytest_randomly"):
        assert importlib.util.find_spec(module) is not None, (
            f"{module} is not installed in the dev .venv; run "
            "`.venv/bin/python -m pip install -r requirements-dev.txt` (#1258)."
        )


def test_plugins_are_registered_with_running_pytest(request):
    """`pytest --cov` / `pytest -p randomly` load with no error (acceptance, #1258)."""
    pm = request.config.pluginmanager
    # Registration names differ from the import names: pytest-cov registers as
    # "pytest_cov", pytest-randomly as "randomly" (its `-p randomly` name).
    for plugin_name in ("pytest_cov", "randomly"):
        assert pm.has_plugin(plugin_name), (
            f"{plugin_name} is installed but not registered with the running pytest; the plugin failed to load."
        )


def test_hypothesis_is_not_installed():
    """`hypothesis` stays deferred (#1246 D3) until a property-test ticket adds it."""
    assert importlib.util.find_spec("hypothesis") is None, (
        "hypothesis is present but #1246 D3 deferred it — it must not be added without its "
        "own approving ticket (see #1258 'Out of scope')."
    )
