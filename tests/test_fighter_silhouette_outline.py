"""#564: the fighter outline traces the whole cat silhouette (body + ears + tail)
and sits BEHIND the sprite, rather than the #546 torso-box rect drawn on top.

Concretely that means: (a) outline pixels appear around the ears (above the body
rect), (b) the body-rect edge is the sprite's own colour, not the outline — the
outline shows only just *outside* the silhouette, and (c) the tail gets the same
outline. Each assertion is able-to-fail against the old torso-box outline.
"""
import pygame

from pycats import render_battle as rb
from pycats.config import FIGHTER_OUTLINE_COLOR, SCREEN_HEIGHT, SCREEN_WIDTH
from pycats.core.input import InputFrame
from pycats.render_battle import _BODY_PAD_TOP, _BODY_PAD_X, _cat_body_surface
from pycats.sim.runner import build_players, build_stage

_OUT = tuple(FIGHTER_OUTLINE_COLOR)


def _settle():
    """A settled fighter (physics run a few frames so the tail has real segments)."""
    pygame.init()
    platforms = build_stage()
    p1, p2, players = build_players()
    empty = InputFrame(set(), set(), set())
    for _ in range(10):
        for p in players:
            p.update(empty, platforms, pygame.sprite.Group())
    return p1


def _vrect(p):
    w, h = p.fighter.stand_size
    return pygame.Rect(_BODY_PAD_X, _BODY_PAD_TOP, w, h)


def test_outline_wraps_the_ears_above_the_body_rect():
    """The silhouette includes the ears, so outline pixels exist ABOVE the body
    rect top — the torso-box outline (#546) never painted there."""
    p = _settle()
    surf = _cat_body_surface(p)
    vrect = _vrect(p)
    found = False
    for y in range(max(0, vrect.top - rb.FIGHTER_OUTLINE_WIDTH - 8), vrect.top):
        for x in range(vrect.left, vrect.right):
            if tuple(surf.get_at((x, y)))[:3] == _OUT:
                found = True
                break
        if found:
            break
    assert found, "no outline pixels around the ears — outline still boxes the torso only"


def test_outline_is_behind_the_sprite_not_over_the_body_edge():
    """The body-rect edge shows the sprite's own colour (outline is behind it),
    and the ring shows just OUTSIDE the silhouette."""
    p = _settle()
    surf = _cat_body_surface(p)
    vrect = _vrect(p)
    edge = tuple(surf.get_at((vrect.left, vrect.centery)))[:3]
    just_outside = tuple(surf.get_at((vrect.left - 1, vrect.centery)))[:3]
    assert edge != _OUT, "body edge is painted with the outline — it's still drawn over the sprite"
    assert just_outside == _OUT, "no outline ring just outside the body silhouette"


def test_interior_pixel_is_never_overpainted():
    """A deep-interior pixel keeps its body/stripe colour, never the outline."""
    p = _settle()
    surf = _cat_body_surface(p)
    assert tuple(surf.get_at(_vrect(p).center))[:3] != _OUT


def test_tail_gets_the_outline_too():
    """render_tail lays the outline behind the tail segments, so outline-coloured
    pixels appear on the rendered tail (able-to-fail: no tail outline -> none)."""
    p = _settle()
    surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    rb.render_tail(surface, p.tail, (20, 20, 20))  # a dark, low-contrast tail
    bb = surface.get_bounding_rect()  # only the tail's drawn area — keep the scan small
    hits = sum(
        1
        for sx in range(bb.left, bb.right)
        for sy in range(bb.top, bb.bottom)
        if tuple(surface.get_at((sx, sy)))[:3] == _OUT
    )
    assert hits > 0, "tail has no outline pixels"
