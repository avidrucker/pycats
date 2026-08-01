"""game.parse_args() launch-flag parsing (#932).

`main()` drives the pygame loop and can't be unit-run, so the argv parsing is factored into
the pure `parse_args(argv)` (no I/O, no pygame). These tests pin the `--speed` present-rate
slow-motion flag that `main()` plumbs into `App(speed=...)`.
"""

import pytest  # type: ignore

from pycats.game import parse_args


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
