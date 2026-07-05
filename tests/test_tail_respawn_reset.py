"""Issue #41 — a respawn must re-initialize the tail to its rest layout, exactly
as on first load, so it does not wildly swing in from wherever it froze at KO.

The Verlet tail keeps live state (positions + implicit velocity). During the
KO->respawn window the player is dead and tail.update never runs, so the chain
freezes wherever it was when the cat flew off-screen. Without a reset, the next
frame after respawn the hip anchor teleports to the spawn point and the chain
whips across that whole distance.
"""
import math

import pygame as pg

from pycats.config import P1_COLOR, RESPAWN_DELAY_FRAMES, WHITE
from pycats.core.input import InputFrame
from pycats.entities.platform import Platform
from pycats.entities.player import Player

C = {"left": pg.K_a, "right": pg.K_d, "up": pg.K_w,
     "down": pg.K_s, "shield": pg.K_q, "attack": pg.K_e}


def _e():
    return InputFrame(held=set(), pressed=set(), released=set())


def _stage():
    g = pg.sprite.Group()
    g.add(Platform(pg.Rect(200, 400, 600, 20), thin=False))
    return g


def _max_move_over(p, plats, frames):
    prev = [(s.x, s.y) for s in p.tail.segments]
    worst = 0.0
    for _ in range(frames):
        p.update(_e(), plats, pg.sprite.Group())
        cur = [(s.x, s.y) for s in p.tail.segments]
        worst = max(worst, max(math.hypot(c[0] - q[0], c[1] - q[1])
                               for q, c in zip(prev, cur)))
        prev = cur
    return worst


def test_tail_reinitializes_on_respawn_like_first_load():
    # Reference: the tail's settle motion on a fresh first load.
    p_load = Player(x=460, y=360, controls=C, color=P1_COLOR, eye_color=WHITE,
                    char_name="Cat", facing_right=True)
    load_max = _max_move_over(p_load, _stage(), 30)

    # Respawn path: settle, fly off-screen WHILE ALIVE (tail trails out there),
    # KO, wait out the respawn, then measure.
    g = _stage()
    p = Player(x=460, y=360, controls=C, color=P1_COLOR, eye_color=WHITE,
               char_name="Cat", facing_right=True)
    for _ in range(120):
        p.update(_e(), g, pg.sprite.Group())
    for _ in range(30):
        p.rect.centerx += 60
        p.update(_e(), g, pg.sprite.Group())
        if not p.fighter.is_alive:
            break
    assert not p.fighter.is_alive                       # we actually KO'd
    for _ in range(RESPAWN_DELAY_FRAMES + 1):
        p.update(_e(), g, pg.sprite.Group())    # -> _respawn
    respawn_max = _max_move_over(p, g, 30)

    # Post-respawn motion must look like a first load, not a big swing-in.
    assert respawn_max <= load_max + 5.0
