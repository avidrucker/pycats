"""#1324 — game.main seeds the dev-HUD master switch from the dev-mode gate.

B2 reconciliation on #1297: inside dev mode the text dev HUD (#1319) AND the
hit/hurtbox overlay (#219) default ON (backtick then flips both together); outside
dev mode dev_hud stays OFF and the overlay never renders. main() realizes that default
with `set_dev_hud(dev_mode())`, seeded right after `set_dev_mode(resolve_dev_mode(args))`.

Tested by invoking main() with the pygame boot + drive loop stubbed (App.running False,
so no frames run). Able-to-fail: drop the `set_dev_hud(...)` seed line from main() and
test_dev_launch_seeds_dev_hud_on goes red (dev_hud stays at the conftest-reset False).
"""

from pycats import game
from pycats.storage import runtime_settings


class _NoLoopApp:
    """Stand-in for App: constructs, never runs (running False → the drive loop is skipped)."""

    running = False

    def __init__(self, *a, **k):
        pass

    def step(self):  # pragma: no cover - never reached, running is False
        raise AssertionError("drive loop must not run in the boot-seed test")


def _run_main(monkeypatch, tmp_path, argv, dev_env=None):
    """Drive game.main() through its boot prefix with all side-effectful I/O stubbed."""
    monkeypatch.setenv("PYCATS_CONFIG_DIR", str(tmp_path))
    if dev_env is None:
        monkeypatch.delenv("PYCATS_DEV", raising=False)
    else:
        monkeypatch.setenv("PYCATS_DEV", dev_env)
    monkeypatch.setattr(game.sys, "argv", ["pycats", *argv])
    monkeypatch.setattr(game.pygame, "init", lambda: None)
    monkeypatch.setattr(game.pygame.display, "set_caption", lambda *a, **k: None)
    monkeypatch.setattr(game.pygame, "quit", lambda: None)
    monkeypatch.setattr(game.sys, "exit", lambda *a, **k: None)
    monkeypatch.setattr(game.keybind_store, "load_last_used", lambda *a, **k: None)
    monkeypatch.setattr(game.keybind_store, "save_last_used", lambda *a, **k: None)
    monkeypatch.setattr(game, "App", _NoLoopApp)
    game.main()


def test_dev_launch_seeds_dev_hud_on(monkeypatch, tmp_path):
    # --dev → dev_mode True → dev_hud seeded ON (overlay + text HUD default on).
    _run_main(monkeypatch, tmp_path, ["--dev"])
    assert runtime_settings.dev_mode() is True
    assert runtime_settings.dev_hud() is True


def test_dev_env_launch_seeds_dev_hud_on(monkeypatch, tmp_path):
    # PYCATS_DEV truthy has the same effect as --dev.
    _run_main(monkeypatch, tmp_path, [], dev_env="1")
    assert runtime_settings.dev_mode() is True
    assert runtime_settings.dev_hud() is True


def test_default_launch_leaves_dev_hud_off(monkeypatch, tmp_path):
    # No --dev / PYCATS_DEV → dev_mode False → dev_hud stays OFF (shipping build).
    _run_main(monkeypatch, tmp_path, [])
    assert runtime_settings.dev_mode() is False
    assert runtime_settings.dev_hud() is False
