"""Guard: importing test_hold_esc_quit must not mutate PYCATS_CONFIG_DIR (#1257).

The module used to write ``os.environ["PYCATS_CONFIG_DIR"] = <tmp>`` at import
time and never restore it, leaking the override into every test collected after
it in the same process (the #345 env-at-import class). This guard re-executes
the module under a throwaway name and asserts the env var is unchanged across the
exec — order-independent (it snapshots around its own fresh exec) and able to
fail: restore the import-time write and the post-exec value diverges from the
snapshot, reddening this test.
"""

import importlib.util
import os


def _reexec_hold_esc_quit():
    """Execute tests/test_hold_esc_quit.py fresh under a unique module name."""
    path = os.path.join(os.path.dirname(__file__), "test_hold_esc_quit.py")
    spec = importlib.util.spec_from_file_location("_hold_esc_quit_reexec_1257", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)


def test_import_does_not_mutate_config_dir_env(monkeypatch):
    """A fresh import of test_hold_esc_quit leaves PYCATS_CONFIG_DIR untouched (#1257)."""
    monkeypatch.delenv("PYCATS_CONFIG_DIR", raising=False)
    before = os.environ.get("PYCATS_CONFIG_DIR")

    _reexec_hold_esc_quit()

    after = os.environ.get("PYCATS_CONFIG_DIR")
    assert after == before, (
        "importing tests/test_hold_esc_quit.py mutated PYCATS_CONFIG_DIR "
        f"({before!r} -> {after!r}); the config-dir override must be scoped to a "
        "per-test fixture, not written at module import (#1257, #345 class)."
    )
