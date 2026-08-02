"""Recovery-hook mid-move velocity phase (#973, child of #566 Final Cutter).

Engine capability split out of #969 and ratified under #1066 (phase model C): a
recovery/special move can declare an ordered list of `VelocityPhase`s, and the
engine SETs the fighter's velocity (facing-relative vx, vy) at each phase's
integer `move_frame` threshold — the mechanism behind Final Cutter's rise->plunge
flip. The trigger is a fixed integer frame count (NOT apex-velocity detection,
ruled out on determinism grounds in #1066 Q2), and it is gated off hitstun so a
mid-rise hit's knockback is never clobbered.

These tests drive a GENERIC test fighter carrying a synthetic recovery `up_b`
with a plunge phase — NO per-cat data is wired here (#973 out-of-scope: Birky's
real plunge frame/velocity land on a follow-up once the capability exists). The
custom FighterData is injected via the Player `fighter_data=` seam, so the shared
default cat is never mutated.
"""

import dataclasses
import json

import pygame as pg

from pycats.combat.data import (
    MoveData,
    VelocityPhase,
    _move_from_json,
    _move_to_json,
    load_fighter_data,
)
from pycats.config import P1_COLOR, WHITE
from pycats.core.input import InputFrame
from pycats.entities.platform import Platform
from pycats.entities.player import Player

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

RISE_VY = -15.0  # start burst (rising)
PLUNGE_FRAME = 5  # well inside the move (total = 2+2+10 = 14)
PLUNGE_VY = 20.0  # fast descent — distinct from any gravity value
PLUNGE_VX = 3.0  # facing-relative


def _plunge_fd(facing_vx=PLUNGE_VX):
    up_b = MoveData(
        name="TestPlunge",
        in_air=True,
        startup=2,
        active=2,
        recovery=10,
        hitboxes=(),
        grants_recovery=True,
        recovery_vy=RISE_VY,
        velocity_phases=(VelocityPhase(frame=PLUNGE_FRAME, vx=facing_vx, vy=PLUNGE_VY),),
    )
    return dataclasses.replace(_TESTCAT, moves={**_TESTCAT.moves, "up_b": up_b})


def _frame(held, pressed):
    return InputFrame(held=set(held), pressed=set(pressed), released=set())


def _airborne(facing_right=True, facing_vx=PLUNGE_VX):
    plats = pg.sprite.Group()
    plats.add(Platform(pg.Rect(0, 4000, 960, 40), thin=False))  # floor far below
    p = Player(
        x=300,
        y=100,
        controls=CONTROLS,
        color=P1_COLOR,
        eye_color=WHITE,
        char_name="PlungeCat",
        facing_right=facing_right,
        fighter_data=_plunge_fd(facing_vx),
    )
    for _ in range(3):
        p.update(_frame(set(), set()), plats, pg.sprite.Group())
    assert not p.fighter.on_ground, "fixture precondition: airborne"
    return p, plats


def _up_b(p, plats):
    p.update(_frame({UP, SPECIAL}, {UP, SPECIAL}), plats, pg.sprite.Group())


def _step_to_frame(p, plats, target):
    """Drive frames until the move clock reaches `target`; return the vel at that frame."""
    for _ in range(60):
        if p.move_frame >= target:
            break
        p.update(_frame(set(), set()), plats, pg.sprite.Group())
    return p


# ---------------------------------------------------------------------------
# Engine: the mid-move velocity flip (able-to-fail)
# ---------------------------------------------------------------------------


def test_velocity_phase_flips_velocity_at_its_frame():
    """At PLUNGE_FRAME the engine SETs vy to the plunge value (a downward flip),
    replacing the rising burst — the substance of #973. Before the phase the
    fighter is still rising (vy < 0), so a missing flip leaves vy negative and
    this assertion fails (revert-the-hook check)."""
    p, plats = _airborne()
    _up_b(p, plats)  # move_frame -> 1, rise burst set (vy = RISE_VY)
    assert p.fighter.vel.y < 0, "fixture: rising before the plunge phase"
    _step_to_frame(p, plats, PLUNGE_FRAME)
    assert p.move_frame == PLUNGE_FRAME
    # SET (not added): velocity is exactly the phase value on the trigger frame,
    # before the next frame's gravity acts on it.
    assert p.fighter.vel.y == PLUNGE_VY, f"plunge should SET vy={PLUNGE_VY}, got {p.fighter.vel.y}"


def test_velocity_phase_vx_follows_facing():
    """vx is applied facing-relative (arc support), like recovery_vx."""
    pr, plats = _airborne(facing_right=True)
    _up_b(pr, plats)
    _step_to_frame(pr, plats, PLUNGE_FRAME)
    assert pr.fighter.vel.x > 0, f"right-facing plunge should push +x, got {pr.fighter.vel.x}"

    pl, plats2 = _airborne(facing_right=False)
    _up_b(pl, plats2)
    _step_to_frame(pl, plats2, PLUNGE_FRAME)
    assert pl.fighter.vel.x < 0, f"left-facing plunge should push -x, got {pl.fighter.vel.x}"


def test_velocity_phase_does_not_fire_before_its_frame():
    """The flip is keyed to its exact frame — vy stays negative (rising) on the
    frames before PLUNGE_FRAME."""
    p, plats = _airborne()
    _up_b(p, plats)
    _step_to_frame(p, plats, PLUNGE_FRAME - 1)
    assert p.move_frame == PLUNGE_FRAME - 1
    assert p.fighter.vel.y < PLUNGE_VY, "plunge must not fire early"


def test_velocity_phase_suppressed_during_hitstun():
    """A phase must NOT clobber knockback: while in hitstun the SET is skipped so
    the launch trajectory survives (the #1066 Q2 determinism/correctness gate)."""
    p, plats = _airborne()
    _up_b(p, plats)
    _step_to_frame(p, plats, PLUNGE_FRAME - 1)
    # Simulate a mid-rise hit landing the frame the plunge would fire.
    p.fighter.hurt_timer = 20
    knockback_vy = -30.0
    p.fighter.vel.y = knockback_vy
    p.update(_frame(set(), set()), plats, pg.sprite.Group())
    assert p.move_frame == PLUNGE_FRAME
    assert p.fighter.vel.y != PLUNGE_VY, "plunge must not overwrite knockback velocity during hitstun"


# ---------------------------------------------------------------------------
# Data: serialization round-trip (omit-when-empty; inline when present)
# ---------------------------------------------------------------------------


def test_velocity_phases_omitted_when_empty():
    """A move with no phases (the default) must not emit the key — golden-safe
    'omit == default'."""
    plain = MoveData(name="plain", in_air=False, startup=2, active=2, recovery=4, hitboxes=())
    assert "velocity_phases" not in _move_to_json(plain)


def test_velocity_phases_roundtrip_through_json():
    """A move carrying phases survives serialize -> JSON text -> hydrate byte-equal."""
    move = _plunge_fd().moves["up_b"]
    rebuilt = _move_from_json(json.loads(json.dumps(_move_to_json(move))))
    assert rebuilt == move
    assert rebuilt.velocity_phases == (VelocityPhase(frame=PLUNGE_FRAME, vx=PLUNGE_VX, vy=PLUNGE_VY),)
