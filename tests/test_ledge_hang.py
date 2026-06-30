"""Ledge-hang state (#14, v1 slice).

Automatic grab at a solid stage edge -> ledge_hang (timed intangible hang) ->
neutral getup (up) / drop (down or away) / timeout. One-occupant lockout per edge
(no trump). Spec: docs/superpowers/specs/2026-06-30-ledge-hang-design.md.
"""
import pygame

from pycats.entities.ledge import Ledge, LEFT, RIGHT, ledges_from_platforms
from pycats.entities.platform import Platform
from pycats import config


def _thick(x, y, w, h):
    return Platform(pygame.Rect(x, y, w, h), thin=False)


def _thin(x, y, w, h):
    return Platform(pygame.Rect(x, y, w, h), thin=True)


# --- Task 1: Ledge value + geometry ------------------------------------------

def test_ledges_from_platforms_only_thick_yields_two_edges():
    plats = [_thick(80, 410, 800, 80), _thin(0, 300, 150, 20)]
    ledges = ledges_from_platforms(plats)
    sides = sorted(l.side for l in ledges)
    assert sides == [LEFT, RIGHT]                 # exactly the thick platform's 2 edges
    left = next(l for l in ledges if l.side == LEFT)
    right = next(l for l in ledges if l.side == RIGHT)
    assert (left.ax, left.ay) == (80, 410)        # top-left corner
    assert (right.ax, right.ay) == (880, 410)     # top-right corner


def test_catch_rect_sits_off_stage_side_and_below_lip():
    left = Ledge(LEFT, 80, 410)
    r = left.catch_rect()
    assert r.right == 80 and r.left == 80 - config.LEDGE_CATCH_W   # left of corner
    assert r.top == 410 and r.height == config.LEDGE_CATCH_H        # lip and below
    right = Ledge(RIGHT, 880, 410)
    rr = right.catch_rect()
    assert rr.left == 880 and rr.width == config.LEDGE_CATCH_W      # right of corner


def test_hang_and_getup_positions_and_facing():
    size = (40, 60)
    left = Ledge(LEFT, 80, 410)
    assert left.facing_right() is True                       # face the stage (right)
    assert left.hang_topleft(size) == (80 - 40, 410)         # body off the left lip
    assert left.getup_topleft(size) == (80, 410 - 60)        # standing on the lip
    right = Ledge(RIGHT, 880, 410)
    assert right.facing_right() is False
    assert right.hang_topleft(size) == (880, 410)
    assert right.getup_topleft(size) == (880 - 40, 410 - 60)


def test_away_held_is_off_stage_direction():
    assert Ledge(LEFT, 80, 410).away_held(left_held=True, right_held=False) is True
    assert Ledge(LEFT, 80, 410).away_held(left_held=False, right_held=True) is False
    assert Ledge(RIGHT, 880, 410).away_held(left_held=False, right_held=True) is True
