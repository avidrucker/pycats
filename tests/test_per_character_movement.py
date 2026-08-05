"""Per-character movement constants (#126, follow-up to #123).

Movement (gravity, max-fall, walk/dash/run, jump-velocity, jump-count) and weight
are per-character FighterData, read per-fighter — so archetypes can diverge (Fox
falls faster, Kirby floats, DK is heavier). Walk / dash / run are raw PM units with
px derived at read (#1209, ADR-0011); gravity / max-fall / jump / jump-count keep
their config-global defaults. These tests prove the values are actually *used*.
"""

import pygame
from pygame import Vector2

from pycats.combat.data import Circle, FighterData, Hurtbox
from pycats.combat.units import u
from pycats.config import (
    GRAVITY,
    JUMP_VEL,
    MAX_FALL_SPEED,
    MAX_JUMPS,
)
from pycats.core.physics import apply_gravity
from pycats.systems.movement import step_horizontal

_HB = Hurtbox(circles=(Circle(0, 0, 1),))


def _fd(**kw) -> FighterData:
    """A FighterData with the default-cat speed units (1.1/1.5/1.5 → 6/8/8),
    overridable per test. walk/dash/run are required now — no config fallback."""
    kw.setdefault("walk", 1.1)
    kw.setdefault("dash", 1.5)
    kw.setdefault("run", 1.5)
    return FighterData(hurtbox=_HB, moves={}, **kw)


def test_non_speed_movement_defaults_match_globals():
    """gravity / max_fall / jump_vel / max_jumps still default to today's globals,
    so a cat that omits them (the default cat, the golden sim) is unchanged."""
    fd = _fd()
    assert fd.gravity == GRAVITY
    assert fd.max_fall_speed == MAX_FALL_SPEED
    assert fd.jump_vel == JUMP_VEL
    assert fd.max_jumps == MAX_JUMPS


def test_walk_dash_run_derive_px_from_units():
    """The shipped px is derived from the raw unit via u() — the default-cat units
    1.1/1.5/1.5 land on 6/8/8, today's old MOVE_SPEED/DASH_SPEED."""
    fd = _fd()
    assert (fd.move_speed, fd.dash_speed, fd.run_speed) == (u(1.1), u(1.5), u(1.5)) == (6, 8, 8)


def test_fighter_data_carries_custom_movement():
    """An archetype can override any movement value; speeds via their raw units."""
    fd = _fd(walk=2.0, dash=2.6, run=3.0, gravity=0.9, max_fall_speed=25, jump_vel=-20, max_jumps=5)
    assert (fd.walk, fd.dash, fd.run) == (2.0, 2.6, 3.0)
    assert (fd.move_speed, fd.dash_speed, fd.run_speed) == (u(2.0), u(2.6), u(3.0))
    assert (fd.gravity, fd.max_fall_speed, fd.jump_vel, fd.max_jumps) == (0.9, 25, -20, 5)


def test_apply_gravity_uses_passed_gravity_and_cap():
    """apply_gravity applies the GIVEN gravity and caps at the GIVEN max-fall —
    not the module globals. Able-to-fail: a hard-coded global would ignore these."""
    assert apply_gravity(Vector2(0, 0), gravity=0.9, max_fall_speed=25).y == 0.9
    # cap: already above the given terminal velocity → clamped to it
    assert apply_gravity(Vector2(0, 100), gravity=0.9, max_fall_speed=25).y == 25


def test_apply_gravity_defaults_to_globals():
    """Omitting the params reproduces the old behaviour exactly."""
    assert apply_gravity(Vector2(0, 0)).y == GRAVITY


def test_step_horizontal_uses_passed_move_speed():
    """A right press accelerates to the GIVEN move_speed (px), a left press to its
    negation. move_speed is a required keyword now (no config default)."""
    vel, facing = step_horizontal(Vector2(0, 0), True, True, False, True, move_speed=10)
    assert vel.x == 10
    vel, facing = step_horizontal(Vector2(0, 0), True, True, True, False, move_speed=10)
    assert vel.x == -10


# --- Fighter threads movement + weight from its FighterData ------------------


def test_fighter_threads_movement_and_weight_from_data():
    """A Fighter reads weight + every movement constant from its FighterData, and
    seeds jumps_remaining from max_jumps. The speed px derive from the raw units."""
    from pycats.entities.fighter import Fighter

    fd = _fd(walk=2.0, dash=2.6, run=3.0, weight=120, gravity=0.9, max_fall_speed=25, jump_vel=-20, max_jumps=5)
    f = Fighter(x=100, y=100, facing_right=True, fighter_data=fd)  # #264/S6: no owner
    assert f.weight == 120
    assert (f.gravity, f.max_fall_speed, f.jump_vel, f.max_jumps) == (0.9, 25, -20, 5)
    assert (f.move_speed, f.dash_speed, f.run_speed) == (u(2.0), u(2.6), u(3.0))
    assert f.jumps_remaining == 5


_CONTROLS = dict(
    left=pygame.K_a,
    right=pygame.K_d,
    up=pygame.K_w,
    down=pygame.K_s,
    attack=pygame.K_v,
    special=pygame.K_c,
    shield=pygame.K_x,
)


def test_player_uses_its_fighter_data_gravity_in_physics():
    """End-to-end wiring: an airborne Player with custom-gravity FighterData
    accelerates by THAT gravity each frame — proving fighter_physics passes the
    fighter's gravity, not the global. Able-to-fail: the global (0.5) would give
    a different delta."""
    from pycats.entities import Player
    from pycats.entities.fighter_physics import step_physics

    fast = _fd(gravity=2.0, max_fall_speed=99)
    p = Player(100, 100, _CONTROLS, (255, 160, 64), eye_color=(0, 0, 0), char_name="custom", fighter_data=fast)
    p.fighter.on_ground = False
    p.fighter.vel.y = 0.0
    step_physics(p, [], set())
    assert p.fighter.vel.y == 2.0
