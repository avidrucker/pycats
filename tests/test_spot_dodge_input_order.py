"""Issue #6 — a spot dodge must fire regardless of down/shield press ORDER.

Three input orders must all reach the same ground spot dodge:
  - simultaneous: down+shield on one frame   (already worked)
  - shield-first: shield held, then down      (already worked)
  - down-first:   down held, then shield      (#6: regressed to a plain shield)

The down-first case is the bug: holding DOWN then pressing SHIELD entered the
shield state instead of triggering a spot dodge.
"""
import pygame as pg

from pycats.config import P1_COLOR, WHITE
from pycats.core.input import InputFrame
from pycats.entities.platform import Platform
from pycats.entities.player import Player

CONTROLS = {
    "left": pg.K_a, "right": pg.K_d, "up": pg.K_w,
    "down": pg.K_s, "shield": pg.K_q, "attack": pg.K_e,
}
DOWN, SHIELD = pg.K_s, pg.K_q


def _make_player():
    platforms = pg.sprite.Group()
    platforms.add(Platform(pg.Rect(600, 400, 200, 20), thin=False))  # thick
    p = Player(x=700, y=400, controls=CONTROLS, color=P1_COLOR, eye_color=WHITE,
               char_name="OrderCat", facing_right=True)
    p.update(InputFrame(held=set(), pressed=set(), released=set()),
             platforms, pg.sprite.Group())  # settle on ground
    return p, platforms


def _frame(held, pressed):
    return InputFrame(held=set(held), pressed=set(pressed), released=set())


def _is_ground_spot_dodge(p):
    return p.fighter.dodge_timer > 0 and p.state == "dodge" and p.fighter.spot_dodge_shield_held


def test_simultaneous_down_shield_spot_dodges():
    p, plats = _make_player()
    p.update(_frame({DOWN, SHIELD}, {DOWN, SHIELD}), plats, pg.sprite.Group())
    assert _is_ground_spot_dodge(p)


def test_shield_first_then_down_spot_dodges():
    p, plats = _make_player()
    p.update(_frame({SHIELD}, {SHIELD}), plats, pg.sprite.Group())       # shield first
    p.update(_frame({SHIELD, DOWN}, {DOWN}), plats, pg.sprite.Group())   # then down
    assert _is_ground_spot_dodge(p)


def test_down_first_then_shield_spot_dodges():
    """The #6 regression: down held, then shield pressed."""
    p, plats = _make_player()
    p.update(_frame({DOWN}, {DOWN}), plats, pg.sprite.Group())           # down first
    p.update(_frame({DOWN, SHIELD}, {SHIELD}), plats, pg.sprite.Group()) # then shield
    assert _is_ground_spot_dodge(p)
