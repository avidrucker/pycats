"""#396 (slice 2a of #388): the dash-state machinery — `dash_speed` + `dash_timer`
+ `dash` chart leaf + `_start_dash()` seam, mirroring the dodge pattern. The
double-tap trigger that calls `_start_dash` is slice 2b; here the seam is driven
directly, and nothing in the default path starts a dash (golden-safe).
"""

import pygame
from helpers import P1
from helpers import mk_player as _mk_player

from pycats.combat.data import load_fighter_data
from pycats.combat.units import u
from pycats.config import DASH_DURATION

pygame.init()

# Default-cat shipped px, derived from its datamine units (#1209): walk 1.1u → 6,
# dash 1.5u → 8. The MOVE_SPEED/DASH_SPEED globals were removed in the re-pin.
_WALK_PX = u(1.1)
_DASH_PX = u(1.5)

# ---- the scalar ----


def test_fighter_data_has_dash_speed_default():
    fd = load_fighter_data("default")
    assert fd.dash_speed == _DASH_PX
    # a fighter reads it like move_speed
    p = _mk_player()
    assert p.fighter.dash_speed == _DASH_PX


# ---- the _start_dash seam ----


def test_start_dash_sets_timer_velocity_and_facing():
    p = _mk_player()
    p.fighter._start_dash(1)
    assert p.fighter.dash_timer == DASH_DURATION
    assert p.fighter.vel.x == _DASH_PX
    assert p.fighter.facing_right is True
    # left dash
    p2 = _mk_player()
    p2.fighter._start_dash(-1)
    assert p2.fighter.vel.x == -_DASH_PX
    assert p2.fighter.facing_right is False


# ---- the dash chart leaf ----


def test_dash_state_entered_while_timer_positive():
    p = _mk_player()
    p.fighter.on_ground = True
    p.fighter._start_dash(1)
    p.engine.tick(None)
    assert p.state == "dash"


def test_dash_exits_to_walk_or_idle_when_timer_hits_zero():
    p = _mk_player()
    p.fighter.on_ground = True
    p.fighter._start_dash(1)
    p.engine.tick(None)
    assert p.state == "dash"
    # drain the timer (the aggregate owns the decrement, like dodge_timer)
    for _ in range(DASH_DURATION):
        p.fighter.tick_action_timers()
    assert p.fighter.dash_timer == 0
    p.engine.tick(None)
    assert p.state != "dash"  # → walk (still moving) or idle


def test_dash_timer_decrements_in_tick_action_timers():
    p = _mk_player()
    p.fighter._start_dash(1)
    before = p.fighter.dash_timer
    p.fighter.tick_action_timers()
    assert p.fighter.dash_timer == before - 1


# ---- movement applies dash_speed while dashing ----


def test_handle_move_uses_dash_speed_while_dashing():
    p = _mk_player()
    p.fighter.on_ground = True
    p.fighter._start_dash(1)  # dash_timer > 0
    p.handle_move({P1["right"]})  # hold right while dashing
    assert p.fighter.vel.x == _DASH_PX

    # once the dash timer is drained, held movement falls back to walk speed
    q = _mk_player()
    q.fighter.on_ground = True
    assert q.fighter.dash_timer == 0
    q.handle_move({P1["right"]})
    assert q.fighter.vel.x == _WALK_PX


# ---- golden-safety: the default path never dashes ----


def test_default_moving_fighter_is_walk_not_dash():
    # a fighter that simply moves (no _start_dash) is in `walk`, never `dash`.
    p = _mk_player()
    p.fighter.on_ground = True
    p.fighter.vel.x = 5
    p.engine.tick(None)
    assert p.state == "walk"
    assert p.fighter.dash_timer == 0
