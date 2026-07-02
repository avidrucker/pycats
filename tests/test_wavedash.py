"""Wavedash — diagonal-down air dodge into the ground (#202, follow-up to #184).

#184 landed the PM-faithful air dodge core (SET-momentum + helpless/special-fall).
This pins the additive wavedash layer:

- a *diagonal-down* air dodge (shield + direction + down, airborne) sets velocity at
  an angle below horizontal (SmashWiki: ~17.1°), not a flat horizontal burst;
- landing during/after that dodge cancels into a grounded slide that decays under
  GROUND_FRICTION (the waveland);
- the post-waveland fighter is locked out of actions for a landing-lag window, then
  recovers to idle.

Pure-horizontal and neutral air dodges (no down component) keep their #184 behaviour
and are pinned in tests/test_air_dodge_helpless.py.

Canon source (#215): the Melee decomp `ftCo_EscapeAir.c` + meleelight `ESCAPEAIR.js`
give the air-dodge model — neutral → (0,0); directional → `escapeair_force × (cosθ,sinθ)`
with `escapeair_force` = 3.1 u/f → `DODGE_AIR_SPEED` = round(3.1 × 5.4) = 17 (pinned #222).
These tests assert magnitude *relative to* DODGE_AIR_SPEED, so they pin the model, not a
literal — robust across a future tuning change.
"""
import pygame as pg

from pycats.entities.player import Player
from pycats.entities.platform import Platform
from pycats.core.input import InputFrame
import math

from pycats.config import (
    P1_COLOR, WHITE, DODGE_AIR_SPEED, WAVEDASH_LANDING_LAG, WAVEDASH_ANGLE_DEG,
)

CONTROLS = {
    "left": pg.K_a, "right": pg.K_d, "up": pg.K_w,
    "down": pg.K_s, "shield": pg.K_q, "attack": pg.K_e,
}
SHIELD, RIGHT, LEFT, UP, DOWN = pg.K_q, pg.K_d, pg.K_a, pg.K_w, pg.K_s


def _frame(held, pressed):
    return InputFrame(held=set(held), pressed=set(pressed), released=set())


def _airborne(floor_y, x=300, y=100):
    """An airborne player with the floor `floor_y` px down."""
    plats = pg.sprite.Group()
    plats.add(Platform(pg.Rect(0, floor_y, 960, 40), thin=False))
    p = Player(x=x, y=y, controls=CONTROLS, color=P1_COLOR, eye_color=WHITE,
               char_name="WaveCat", facing_right=True)
    for _ in range(3):
        p.update(_frame(set(), set()), plats, pg.sprite.Group())
    assert not p.fighter.on_ground, "fixture precondition: airborne"
    return p, plats


def _step_until_landed(p, plats, max_frames=120):
    """Idle-step until the fighter touches ground; return the landing-frame state."""
    for _ in range(max_frames):
        p.update(_frame(set(), set()), plats, pg.sprite.Group())
        if p.fighter.on_ground:
            return p.state
    raise AssertionError("fighter never landed within the window")


def test_diagonal_down_air_dodge_sets_angled_burst():
    """A shield+right+down air dodge sets velocity DOWN-and-right (angled), not flat."""
    p, plats = _airborne(floor_y=2000)  # lots of room: dodge plays out in the air
    p.update(_frame({SHIELD, RIGHT, DOWN}, {SHIELD, RIGHT, DOWN}),
             plats, pg.sprite.Group())
    assert p.state == "dodge"
    expected_vy = DODGE_AIR_SPEED * math.sin(math.radians(WAVEDASH_ANGLE_DEG))  # ≈ 4.1
    expected_vx = DODGE_AIR_SPEED * math.cos(math.radians(WAVEDASH_ANGLE_DEG))  # ≈ 13.4
    # vx is the horizontal component of the angled burst (untouched by gravity this frame)
    assert abs(p.fighter.vel.x - expected_vx) < 0.5, (
        f"diagonal-down dodge vx should be ≈{expected_vx:.1f}, got {p.fighter.vel.x:.2f}"
    )
    # vy must reflect the angled DOWN burst — well beyond the ~0.5 a flat air dodge
    # would show after a single frame of gravity (this is what pins the *angle*).
    assert p.fighter.vel.y >= expected_vy - 0.5, (
        f"diagonal-down dodge should burst DOWNWARD at the wavedash angle "
        f"(vy≈{expected_vy:.1f}+gravity), got vy={p.fighter.vel.y:.2f} — a flat horizontal "
        "air dodge would leave vy at only ~0.5 (one frame of gravity)"
    )


def test_wavedash_produces_grounded_slide_that_decays():
    """Diagonal-down air dodge into the ground → a grounded horizontal slide whose
    speed decays each frame under ground friction (not an instant stop)."""
    p, plats = _airborne(floor_y=190)  # close floor: lands mid-dodge, momentum intact
    p.update(_frame({SHIELD, RIGHT, DOWN}, {SHIELD, RIGHT, DOWN}),
             plats, pg.sprite.Group())
    _step_until_landed(p, plats)
    assert p.fighter.on_ground
    slide0 = p.fighter.vel.x
    assert slide0 > 0.1, f"waveland should keep a forward slide, got vx={slide0}"
    # advance one frame: friction must bleed the slide, not zero it instantly
    p.update(_frame(set(), set()), plats, pg.sprite.Group())
    slide1 = p.fighter.vel.x
    assert 0 < slide1 < slide0, f"slide should decay under friction: {slide0} -> {slide1}"
    # and eventually settle to a stop
    for _ in range(60):
        p.update(_frame(set(), set()), plats, pg.sprite.Group())
    assert p.fighter.vel.x == 0, f"slide should settle to 0, got {p.fighter.vel.x}"


def test_waveland_locks_actions_for_landing_lag_then_recovers():
    """After a waveland the fighter is in landing-lag (actions locked) for the lag
    window, then recovers to idle. A jump during the lag is ignored."""
    p, plats = _airborne(floor_y=190)
    p.update(_frame({SHIELD, RIGHT, DOWN}, {SHIELD, RIGHT, DOWN}),
             plats, pg.sprite.Group())
    landed_state = _step_until_landed(p, plats)
    assert landed_state == "landing_lag", (
        f"landing from a wavedash should enter landing_lag, got {landed_state!r}"
    )
    # a jump press during landing lag is ignored and consumes no jump
    jumps_before = p.fighter.jumps_remaining
    p.update(_frame({UP}, {UP}), plats, pg.sprite.Group())
    assert p.state == "landing_lag", "jump must be locked out during landing lag"
    assert p.fighter.jumps_remaining == jumps_before, "landing lag must not consume a jump"
    # within the lag window it recovers to idle
    for _ in range(WAVEDASH_LANDING_LAG + 2):
        p.update(_frame(set(), set()), plats, pg.sprite.Group())
    assert p.state == "idle", f"should recover to idle after the lag window, got {p.state!r}"
