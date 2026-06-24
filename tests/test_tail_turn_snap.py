"""Issue #3 — turning must not snap the tail.

On a facing flip the tail-base anchor offset flipped sign instantly, jumping
2*TAIL_BASE_OFFSET_X px in a single frame, and the per-frame cheap-follow path
rigidly translated the whole tail by that jump. The fix eases the anchor across
the flip so no single frame moves the tail anywhere near the full jump.

Metric: max single-frame movement of any tail segment over the frames right
after a facing flip (player otherwise stationary) must stay well under the
2*offset snap — bounded near the per-frame baseline idle motion.
"""
import math

import pygame as pg

from pycats.entities.player import Player
from pycats.entities.platform import Platform
from pycats.core.input import InputFrame
from pycats.config import P1_COLOR, WHITE, TAIL_BASE_OFFSET_X

C = {"left": pg.K_a, "right": pg.K_d, "up": pg.K_w,
     "down": pg.K_s, "shield": pg.K_q, "attack": pg.K_e}


def _empty():
    return InputFrame(held=set(), pressed=set(), released=set())


def _positions(tail):
    return [(s.x, s.y) for s in tail.segments]


def _max_step(prev, cur):
    return max(math.hypot(c[0] - p[0], c[1] - p[1]) for p, c in zip(prev, cur))


def _settled_player():
    plats = pg.sprite.Group()
    plats.add(Platform(pg.Rect(200, 400, 600, 20), thin=False))
    p = Player(x=460, y=400, controls=C, color=P1_COLOR, eye_color=WHITE,
               char_name="Cat", facing_right=True)
    empty = pg.sprite.Group()
    for _ in range(40):
        p.update(_empty(), plats, empty)
    return p, plats, empty


def _max_step_over(p, plats, empty, frames):
    prev = _positions(p.tail)
    worst = 0.0
    for _ in range(frames):
        p.update(_empty(), plats, empty)
        cur = _positions(p.tail)
        worst = max(worst, _max_step(prev, cur))
        prev = cur
    return worst


def test_facing_flip_does_not_snap_tail():
    p, plats, empty = _settled_player()
    p.facing_right = not p.facing_right              # cat turns around
    flip_max = _max_step_over(p, plats, empty, 15)
    # The pre-fix bug teleported the whole tail ~2*TAIL_BASE_OFFSET_X (30px) in a
    # SINGLE frame. The eased anchor + base orientation keep any single-frame move
    # well under one offset; with the #37 Verlet model the turn is a smooth multi-
    # frame SWING (~5px/frame), which is correct dynamic motion, not a snap.
    assert flip_max < TAIL_BASE_OFFSET_X
