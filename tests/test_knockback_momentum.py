"""Issue #8 — a moving defender's momentum must COMBINE with knockback, not be
zeroed, in both the moving and stationary cases.

Two coupled defects:
  (a) receive_hit overwrote velocity with knockback (`=`), discarding the
      defender's existing horizontal momentum.
  (b) the hit lands after the frame's engine.tick, so the FSM flips to "hurt"
      one frame late — letting one extra handle_move clobber the horizontal
      knockback with walk speed when a direction is held.

The exact PM knockback magnitude is an open research thread (#24); these tests
assert the COMBINE-don't-zero behaviour, not a specific coefficient.
"""
import math

import pygame as pg

from pycats.entities.player import Player
from pycats.entities.platform import Platform
from pycats.entities.attack import Attack
from pycats.core.input import InputFrame
from pycats.config import (P1_COLOR, P2_COLOR, WHITE, MOVE_SPEED,
                           KNOCKBACK_BASE, KNOCKBACK_SCALE, HIT_DAMAGE)

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


def _expected_kb(percent_after):
    # knockback magnitude after the hit raises percent by HIT_DAMAGE
    return KNOCKBACK_BASE + KNOCKBACK_SCALE * percent_after


def test_receive_hit_combines_horizontal_momentum():
    """A stationary `=` overwrite is fine, but existing momentum must be added."""
    attacker, defender, *_ = _setup(defender_vel_x=5.0)
    atk = Attack(owner=attacker, damage=HIT_DAMAGE, angle=0)  # horizontal +x
    defender.receive_hit(atk)
    kb = _expected_kb(defender.percent)
    assert defender.vel.x == 5.0 + kb  # momentum (5) COMBINED with knockback


def test_stationary_knockback_unchanged():
    """With no prior momentum, combine == plain knockback (no regression)."""
    attacker, defender, *_ = _setup(defender_vel_x=0.0)
    atk = Attack(owner=attacker, damage=HIT_DAMAGE, angle=0)
    defender.receive_hit(atk)
    assert defender.vel.x == _expected_kb(defender.percent)


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
    atk = Attack(owner=attacker, damage=HIT_DAMAGE, angle=0)
    defender.receive_hit(atk)
    # frame after the hit, direction still held
    defender.update(_frame(held), plats, empty)
    assert defender.vel.x > MOVE_SPEED + 0.5  # knockback survived, not clobbered
