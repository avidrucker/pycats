"""Per-character movement constants (#126, follow-up to #123).

Movement (gravity, max-fall, move-speed, jump-velocity, jump-count) and weight
move from global config into per-character FighterData, read per-fighter — so
archetypes can diverge (Fox falls faster, Kirby floats, DK is heavier). For the
default cat / Nalio the values equal today's globals, so the sim is unchanged
(goldens stay green); these tests prove the values are actually *used* when they
differ.
"""
import pygame
from pygame import Vector2

from pycats.config import (
    GRAVITY, MAX_FALL_SPEED, MOVE_SPEED, JUMP_VEL, MAX_JUMPS,
)
from pycats.combat.data import FighterData, Hurtbox, Circle
from pycats.core.physics import apply_gravity
from pycats.systems.movement import step_horizontal

_HB = Hurtbox(circles=(Circle(0, 0, 1),))


def test_fighter_data_movement_defaults_match_globals():
    """A FighterData that doesn't specify movement keeps today's globals — so
    the default cat (and the golden sim) is unchanged."""
    fd = FighterData(hurtbox=_HB, moves={})
    assert fd.gravity == GRAVITY
    assert fd.max_fall_speed == MAX_FALL_SPEED
    assert fd.move_speed == MOVE_SPEED
    assert fd.jump_vel == JUMP_VEL
    assert fd.max_jumps == MAX_JUMPS


def test_fighter_data_carries_custom_movement():
    """An archetype can override any movement value."""
    fd = FighterData(hurtbox=_HB, moves={}, gravity=0.9, max_fall_speed=25,
                     move_speed=10, jump_vel=-20, max_jumps=5)
    assert (fd.gravity, fd.max_fall_speed, fd.move_speed, fd.jump_vel,
            fd.max_jumps) == (0.9, 25, 10, -20, 5)


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
    """A right press accelerates to the GIVEN move_speed, not the global."""
    vel, facing = step_horizontal(Vector2(0, 0), True, True, False, True,
                                  move_speed=10)
    assert vel.x == 10
    vel, facing = step_horizontal(Vector2(0, 0), True, True, True, False,
                                  move_speed=10)
    assert vel.x == -10


def test_step_horizontal_defaults_to_global_move_speed():
    vel, _ = step_horizontal(Vector2(0, 0), True, True, False, True)
    assert vel.x == MOVE_SPEED


# --- Fighter threads movement + weight from its FighterData ------------------

class _Owner:
    SIZE = (40, 60)


def test_fighter_threads_movement_and_weight_from_data():
    """A Fighter reads weight + every movement constant from its FighterData,
    and seeds jumps_remaining from max_jumps. Able-to-fail: a hard-coded global
    (the old behaviour) would ignore these custom values."""
    from pycats.entities.fighter import Fighter
    fd = FighterData(hurtbox=_HB, moves={}, weight=120, gravity=0.9,
                     max_fall_speed=25, move_speed=10, jump_vel=-20, max_jumps=5)
    f = Fighter(_Owner(), x=100, y=100, facing_right=True, fighter_data=fd)
    assert f.weight == 120
    assert (f.gravity, f.max_fall_speed, f.move_speed, f.jump_vel,
            f.max_jumps) == (0.9, 25, 10, -20, 5)
    assert f.jumps_remaining == 5


_CONTROLS = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w,
                 down=pygame.K_s, attack=pygame.K_v, special=pygame.K_c,
                 shield=pygame.K_x)


def test_player_uses_its_fighter_data_gravity_in_physics():
    """End-to-end wiring: an airborne Player with custom-gravity FighterData
    accelerates by THAT gravity each frame — proving fighter_physics passes the
    fighter's gravity, not the global. Able-to-fail: the global (0.5) would give
    a different delta."""
    from pycats.entities import Player
    from pycats.entities.fighter_physics import step_physics

    fast = FighterData(hurtbox=_HB, moves={}, gravity=2.0, max_fall_speed=99)
    p = Player(100, 100, _CONTROLS, (255, 160, 64), eye_color=(0, 0, 0),
               char_name="custom", fighter_data=fast)
    p.fighter.on_ground = False
    p.fighter.vel.y = 0.0
    step_physics(p, [], set())
    assert p.fighter.vel.y == 2.0
