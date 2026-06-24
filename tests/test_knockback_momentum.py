"""Issue #8 — a moving defender's momentum must COMBINE with knockback, not be
zeroed, in both the moving and stationary cases.

Two coupled defects:
  (a) receive_hit overwrote velocity with knockback (`=`), discarding the
      defender's existing horizontal momentum.
  (b) the hit lands after the frame's engine.tick, so the FSM flips to "hurt"
      one frame late — letting one extra handle_move clobber the horizontal
      knockback with walk speed when a direction is held.

These tests assert the COMBINE-don't-zero behaviour. The knockback magnitude is
now the authentic Brawl/PM formula (#40); the expected launch is computed with the
same pure `knockback()` so the assertions track the model, not a hard-coded number.
"""
import math

import pygame as pg
import pytest

from pycats.entities.player import Player
from pycats.entities.platform import Platform
from pycats.entities.attack import Attack
from pycats.core.input import InputFrame
from pycats.combat.knockback import knockback
from pycats.config import (P1_COLOR, P2_COLOR, WHITE, MOVE_SPEED,
                           KNOCKBACK_VELOCITY_SCALE, HIT_DAMAGE)

# The default cat jab's knockback fields (see characters/default_cat.py). These
# tests build a fallback Attack (no Hitbox), so set them explicitly to exercise a
# real, non-zero launch.
_JAB_BKB = 30.0
_JAB_KBG = 100.0

CONTROLS = {"left": pg.K_a, "right": pg.K_d, "up": pg.K_w,
            "down": pg.K_s, "shield": pg.K_q, "attack": pg.K_e}
RIGHT = pg.K_d


def _frame(held):
    return InputFrame(held=set(held), pressed=set(), released=set())


def _setup(defender_vel_x=0.0):
    plats = pg.sprite.Group()
    plats.add(Platform(pg.Rect(200, 400, 600, 20), thin=False))
    attacker = Player(x=360, y=400, controls=CONTROLS, color=P1_COLOR,
                      eye_color=WHITE, char_name="Atk", facing_right=True)
    defender = Player(x=420, y=400, controls=CONTROLS, color=P2_COLOR,
                      eye_color=WHITE, char_name="Def", facing_right=True)
    empty = pg.sprite.Group()
    for _ in range(2):  # settle on platform
        attacker.update(_frame([]), plats, empty)
        defender.update(_frame([]), plats, empty)
    defender.vel.x = defender_vel_x
    return attacker, defender, plats, empty


def _expected_launch(defender):
    # Launch applied to vel.x: authentic KB * velocity scale (angle 0 -> all horizontal).
    kb = knockback(defender.percent, HIT_DAMAGE, defender.weight, _JAB_BKB, _JAB_KBG)
    return kb * KNOCKBACK_VELOCITY_SCALE


def _jab(attacker):
    atk = Attack(owner=attacker, damage=HIT_DAMAGE, angle=0)  # horizontal +x
    atk.base_knockback, atk.knockback_growth = _JAB_BKB, _JAB_KBG
    return atk


def test_receive_hit_combines_horizontal_momentum():
    """A stationary `=` overwrite is fine, but existing momentum must be added."""
    attacker, defender, *_ = _setup(defender_vel_x=5.0)
    defender.receive_hit(_jab(attacker))
    # momentum (5) COMBINED with knockback, not overwritten
    assert defender.vel.x == pytest.approx(5.0 + _expected_launch(defender))


def test_stationary_knockback_unchanged():
    """With no prior momentum, combine == plain knockback (no regression)."""
    attacker, defender, *_ = _setup(defender_vel_x=0.0)
    defender.receive_hit(_jab(attacker))
    assert defender.vel.x == pytest.approx(_expected_launch(defender))


def test_hitstun_is_computed_from_knockback_not_fixed():
    """#40: hurt_timer comes from hitstun_frames(KB), not the old fixed 12."""
    from pycats.combat.knockback import knockback, hitstun_frames
    attacker, defender, *_ = _setup(defender_vel_x=0.0)
    defender.receive_hit(_jab(attacker))
    kb = knockback(defender.percent, HIT_DAMAGE, defender.weight, _JAB_BKB, _JAB_KBG)
    assert defender.hurt_timer == hitstun_frames(kb)
    assert defender.hurt_timer != 12  # the retired HURT_TIME constant


def test_moving_knockback_not_clobbered_by_input():
    """End-to-end (game-loop order): a moving, still-holding-right defender keeps
    its combined knockback on the frame after the hit instead of collapsing to
    walk speed."""
    attacker, defender, plats, empty = _setup()
    held = [RIGHT]
    for _ in range(6):  # ramp defender up to walk speed
        defender.update(_frame(held), plats, empty)
    # hit frame: update first, then receive_hit (mirrors game.py order)
    attacker.update(_frame([]), plats, empty)
    defender.update(_frame(held), plats, empty)
    defender.receive_hit(_jab(attacker))
    # frame after the hit, direction still held
    defender.update(_frame(held), plats, empty)
    assert defender.vel.x > MOVE_SPEED + 0.5  # knockback survived, not clobbered
