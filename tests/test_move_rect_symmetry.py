"""Repro for #949 — every character must move symmetrically left vs right.

Bug: `core.physics.move_rect` adds a float velocity straight into pygame's integer
`Rect`, which truncates toward zero. At a positive on-stage x that makes a leftward
step `ceil(|vel.x|)` and a rightward step `floor(|vel.x|)` — a 1px/frame leftward
bias whenever vel.x is fractional. The agreed rule (missing here) is to round a raw
pixel value symmetrically *before* pygame consumes it.

Requirement under test (must hold for EVERY character, EVERY ground regime):
  1. realized left displacement == realized right displacement over N frames, and
  2. the fighter takes the SAME number of frames to travel 200px left as right.

Non-vacuous by construction:
  * integer-speed cats (nalio/narz/birky/default, and Gnok's run=8) satisfy both
    today → GREEN, proving the asserts are meaningful and not always-failing;
  * Gnok's fractional walk (6.48) and dash (9.72) violate both today → RED,
    reproducing the bug. All parametrizations go GREEN once move_rect rounds
    the position at the pygame boundary (fix tracked on this ticket, #979).
"""

import pygame as pg
import pytest

from pycats.combat.data import load_fighter_data
from pycats.core.physics import move_rect

# Every shipped/selectable character (testcat == the default cat).
CATS = ["nalio", "narz", "birky", "gnok", "testcat"]
REGIMES = ["walk", "dash", "run"]
START_X = 480  # mid-stage; the whole play region (and ±200px from here) is positive x


def _speed(cat: str, regime: str) -> float:
    fd = load_fighter_data(cat)
    return {"walk": fd.move_speed, "dash": fd.dash_speed, "run": fd.run_speed}[regime]


def _displacement(vel_x: float, frames: int) -> int:
    """Absolute integer distance covered after driving move_rect `frames` times."""
    r = pg.Rect(START_X, 0, 10, 10)
    for _ in range(frames):
        move_rect(r, pg.Vector2(vel_x, 0))
    return abs(r.x - START_X)


def _frames_to_travel(vel_x: float, distance: int) -> int:
    """How many frames to cover at least `distance` px at constant vel_x."""
    r = pg.Rect(START_X, 0, 10, 10)
    frames = 0
    while abs(r.x - START_X) < distance:
        move_rect(r, pg.Vector2(vel_x, 0))
        frames += 1
        assert frames < 100_000, "runaway: fighter never reached the target distance"
    return frames


@pytest.mark.parametrize("cat", CATS)
@pytest.mark.parametrize("regime", REGIMES)
def test_left_right_same_realized_velocity(cat, regime):
    """Same distance covered moving left as right, over the same frame count."""
    speed = _speed(cat, regime)
    frames = 30
    left = _displacement(-speed, frames)
    right = _displacement(speed, frames)
    assert left == right, f"{cat} {regime} @ {speed}px/f: left={left}px right={right}px over {frames}f"


@pytest.mark.parametrize("cat", CATS)
@pytest.mark.parametrize("regime", REGIMES)
def test_left_right_same_time_to_travel_200px(cat, regime):
    """Same number of frames to travel 200px left as 200px right."""
    speed = _speed(cat, regime)
    left_frames = _frames_to_travel(-speed, 200)
    right_frames = _frames_to_travel(speed, 200)
    assert left_frames == right_frames, (
        f"{cat} {regime} @ {speed}px/f: {left_frames}f to go 200px left vs {right_frames}f right"
    )
