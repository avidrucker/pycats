"""Issue #2 — after a ground dodge roll the fighter faces OPPOSITE to the roll
travel direction (Project M behaviour).

Per SmashWiki (Roll): a forward roll turns the character around, a back roll
keeps facing — and both end facing opposite to the travel direction. So the
end-state rule, independent of the starting facing, is:
    roll left  (travel -x) -> face right (facing_right True)
    roll right (travel +x) -> face left  (facing_right False)
"""
import pygame as pg
import pytest

from pycats.config import P1_COLOR, WHITE
from pycats.core.input import InputFrame
from pycats.entities.platform import Platform
from pycats.entities.player import Player

C = {"left": pg.K_a, "right": pg.K_d, "up": pg.K_w,
     "down": pg.K_s, "shield": pg.K_q, "attack": pg.K_e}
LEFT, RIGHT, SHIELD = pg.K_a, pg.K_d, pg.K_q


def _f(held):
    return InputFrame(held=set(held), pressed=set(held), released=set())


def _roll(initial_facing_right, direction_key):
    plats = pg.sprite.Group()
    plats.add(Platform(pg.Rect(200, 400, 600, 20), thin=False))
    p = Player(x=460, y=400, controls=C, color=P1_COLOR, eye_color=WHITE,
               char_name="R", facing_right=initial_facing_right)
    empty = pg.sprite.Group()
    for _ in range(2):
        p.update(_f([]), plats, empty)
    p.fighter.facing_right = initial_facing_right
    p.update(_f([SHIELD, direction_key]), plats, empty)  # shield+dir -> ground roll
    assert p.state == "dodge" and p.fighter.dodge_timer > 0       # a roll actually started
    return p


@pytest.mark.parametrize("initial_facing_right", [True, False])
def test_roll_left_faces_right(initial_facing_right):
    p = _roll(initial_facing_right, LEFT)
    assert p.fighter.facing_right is True   # travel -x -> face +x


@pytest.mark.parametrize("initial_facing_right", [True, False])
def test_roll_right_faces_left(initial_facing_right):
    p = _roll(initial_facing_right, RIGHT)
    assert p.fighter.facing_right is False  # travel +x -> face -x
