"""Generalized up-B / special-recovery engine hook (#578, B1 of #566).

Design: docs/research/2026-07-05-up-b-recovery-spike.md. A move flagged
`grants_recovery` applies an upward velocity burst on start (per-cat
`recovery_vy`/`recovery_vx`) and, when it ends airborne, routes the fighter into
the existing `helpless` state (#184) — locked out until it lands / grabs a ledge.

These tests drive a GENERIC test fighter carrying a recovery `up_b` (no per-cat
data is wired here — Nalio/Birky/Narz up-Bs are B2-B4). The custom FighterData is
injected via the Player `fighter_data=` seam, so the shared default cat is never
mutated.
"""

import dataclasses

import pygame as pg

from pycats.combat.data import MoveData, load_fighter_data
from pycats.config import GRAVITY, P1_COLOR, WHITE
from pycats.core.input import InputFrame
from pycats.entities.platform import Platform
from pycats.entities.player import Player

# The minimal one-move test fixture, loaded by name (#591).
_TESTCAT = load_fighter_data("testcat")

CONTROLS = {
    "left": pg.K_a,
    "right": pg.K_d,
    "up": pg.K_w,
    "down": pg.K_s,
    "shield": pg.K_q,
    "attack": pg.K_e,
    "special": pg.K_c,
}
UP, SPECIAL = pg.K_w, pg.K_c

RECOVERY_VY = -15.0


def _recovery_fd(recovery_vx=0.0):
    up_b = MoveData(
        name="TestRecovery",
        in_air=True,
        startup=2,
        active=2,
        recovery=2,
        hitboxes=(),
        grants_recovery=True,
        recovery_vy=RECOVERY_VY,
        recovery_vx=recovery_vx,
    )
    return dataclasses.replace(_TESTCAT, moves={**_TESTCAT.moves, "up_b": up_b})


def _frame(held, pressed):
    return InputFrame(held=set(held), pressed=set(pressed), released=set())


def _airborne(recovery_vx=0.0, floor_y=2000, facing_right=True):
    plats = pg.sprite.Group()
    plats.add(Platform(pg.Rect(0, floor_y, 960, 40), thin=False))
    p = Player(
        x=300,
        y=100,
        controls=CONTROLS,
        color=P1_COLOR,
        eye_color=WHITE,
        char_name="RecoveryCat",
        facing_right=facing_right,
        fighter_data=_recovery_fd(recovery_vx),
    )
    for _ in range(3):
        p.update(_frame(set(), set()), plats, pg.sprite.Group())
    assert not p.fighter.on_ground, "fixture precondition: airborne"
    return p, plats


def _up_b(p, plats):
    p.update(_frame({UP, SPECIAL}, {UP, SPECIAL}), plats, pg.sprite.Group())


def test_up_b_sets_upward_recovery_burst():
    """up-B SETS a strong upward velocity, replacing downward momentum (not adding).
    Robust to one frame of gravity applied the same tick."""
    p, plats = _airborne()
    p.fighter.vel.y = 8.0  # falling
    _up_b(p, plats)
    assert p.fighter.vel.y < 0, f"up-B should set an upward burst, got vy={p.fighter.vel.y}"
    assert p.fighter.vel.y <= RECOVERY_VY + 2 * GRAVITY, (
        f"burst should be ~{RECOVERY_VY} (SET, not added to +8), got {p.fighter.vel.y}"
    )


def test_up_b_move_ends_in_helpless():
    p, plats = _airborne()
    _up_b(p, plats)
    for _ in range(10):  # move total = 2+2+2 = 6; step past it, still airborne
        p.update(_frame(set(), set()), plats, pg.sprite.Group())
    assert p.state == "helpless", f"recovery move should end in helpless, got {p.state!r}"


def test_second_up_b_locked_during_helpless():
    p, plats = _airborne()
    _up_b(p, plats)
    for _ in range(10):
        p.update(_frame(set(), set()), plats, pg.sprite.Group())
    assert p.state == "helpless"
    vy_before = p.fighter.vel.y  # falling under gravity in helpless
    _up_b(p, plats)  # try to recover again
    assert p.state == "helpless", "a second up-B during helpless must be a no-op"
    assert p.fighter.vel.y >= vy_before - 1, "helpless up-B must not re-apply the upward burst"


def test_up_b_horizontal_component_follows_facing():
    """recovery_vx is applied in the facing direction (arc support for B2-B4)."""
    pr, plats = _airborne(recovery_vx=4.0, facing_right=True)
    _up_b(pr, plats)
    assert pr.fighter.vel.x > 0, f"right-facing up-B should push +x, got {pr.fighter.vel.x}"
    pl, plats2 = _airborne(recovery_vx=4.0, facing_right=False)
    _up_b(pl, plats2)
    assert pl.fighter.vel.x < 0, f"left-facing up-B should push -x, got {pl.fighter.vel.x}"


def test_landing_from_recovery_clears_flag_and_idles():
    p, plats = _airborne(floor_y=260)  # land within the window
    _up_b(p, plats)
    landed = None
    for _ in range(240):
        p.update(_frame(set(), set()), plats, pg.sprite.Group())
        if p.fighter.on_ground:
            landed = p.state
            break
    assert p.fighter.on_ground, "fixture: should land"
    assert landed == "idle", f"recovery should recover to idle on landing, got {landed!r}"
    assert p.fighter.recovery_active is False, "landing must clear recovery_active"
