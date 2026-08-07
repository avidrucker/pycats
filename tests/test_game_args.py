"""game.parse_args() launch-flag parsing (#932) + the dev-mode gate (#1312).

`main()` drives the pygame loop and can't be unit-run, so the argv parsing is factored into
the pure `parse_args(argv)` (no I/O, no pygame). These tests pin the `--speed` present-rate
slow-motion flag that `main()` plumbs into `App(speed=...)`, and the `--dev` / `PYCATS_DEV`
dev-mode gate that `main()` resolves via `resolve_dev_mode(args)` into
`runtime_settings.dev_mode` (ruling A1 on #1297).
"""

import pytest  # type: ignore

from pycats.game import parse_args, resolve_dev_mode


def test_speed_defaults_to_real_time():
    assert parse_args([]).speed == 1.0


def test_speed_half():
    assert parse_args(["--speed", "0.5"]).speed == 0.5


def test_speed_quarter():
    assert parse_args(["--speed", "0.25"]).speed == 0.25


def test_speed_is_a_float():
    assert isinstance(parse_args(["--speed", "0.5"]).speed, float)


def test_non_numeric_speed_is_rejected():
    with pytest.raises(SystemExit):
        parse_args(["--speed", "slow"])


# --- dev-mode gate (#1312) ---------------------------------------------------
# resolve_dev_mode(args) = args.dev OR truthy PYCATS_DEV (mirrors dev_log.enabled()).
# These are able-to-fail: drop `--dev` from parse_args and test_dev_flag_* go red;
# drop the env clause from resolve_dev_mode and test_dev_env_* / test_dev_both_off go red.


def test_dev_defaults_off():
    assert parse_args([]).dev is False


def test_dev_flag_sets_the_arg():
    assert parse_args(["--dev"]).dev is True


def test_dev_flag_on_resolves_true(monkeypatch):
    monkeypatch.delenv("PYCATS_DEV", raising=False)
    assert resolve_dev_mode(parse_args(["--dev"])) is True


def test_dev_env_on_resolves_true(monkeypatch):
    """PYCATS_DEV alone (no --dev) turns dev mode on — the env door."""
    monkeypatch.setenv("PYCATS_DEV", "1")
    assert resolve_dev_mode(parse_args([])) is True


def test_dev_both_off_resolves_false(monkeypatch):
    """No flag, no env → dev mode off (the shipping/default launch)."""
    monkeypatch.delenv("PYCATS_DEV", raising=False)
    assert resolve_dev_mode(parse_args([])) is False


def test_dev_arg_and_env_set_the_same_flag(monkeypatch):
    """Both doors set the one owner: either alone, or both together, resolves True."""
    monkeypatch.setenv("PYCATS_DEV", "1")
    assert resolve_dev_mode(parse_args(["--dev"])) is True


def test_dev_mode_owner_round_trips():
    """runtime_settings.dev_mode() reflects what set_dev_mode() last wrote (one owner)."""
    from pycats.storage import runtime_settings

    runtime_settings.set_dev_mode(True)
    assert runtime_settings.dev_mode() is True
    runtime_settings.set_dev_mode(False)
    assert runtime_settings.dev_mode() is False
