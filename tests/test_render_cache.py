# tests/test_render_cache.py
"""The cat-body composite cache must be pixel-identical to drawing each frame."""
import pygame
import pytest

from pycats import render_battle as rb
from pycats.config import (
    BG_COLOR,
    FIGHTER_OUTLINE_COLOR,
    FIGHTER_OUTLINE_WIDTH,
    RED,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from pycats.core.input import InputFrame
from pycats.sim.runner import build_players, build_stage

# Re-init font + clear stale render/font caches before each test so a prior
# test's pygame.quit() can't break the pixel-identity assertions (#63).
pytestmark = pytest.mark.usefixtures("render_isolation")


def _direct(surface, p):
    """Replicate the per-frame body draw sequence (pre-cache)."""
    overlay = rb.active_tint(p)
    body = pygame.Surface(p.rect.size)
    body.fill(rb._blend(p.char_color, overlay))  # softened flash, render-time (#75/#109)
    surface.blit(body, p.rect)
    shim = rb._CatShim(p.rect, p.fighter.facing_right, p.char_color, p.eye_color,
                       p.stripe_color, p.char_name, tint=overlay)
    rb.draw_stripes(surface, shim)
    rb.draw_eye(surface, shim)
    rb.draw_eye(surface, shim, eye=False)
    rb.draw_cat_features(surface, shim)
    rb.draw_player_name(surface, shim)
    # Body outline drawn last, mirroring _cat_body_surface (#546).
    pygame.draw.rect(surface, FIGHTER_OUTLINE_COLOR, p.rect, FIGHTER_OUTLINE_WIDTH)


def _cached(surface, p):
    body = rb._cat_body_surface(p)
    surface.blit(body, (p.rect.x - rb._BODY_PAD_X, p.rect.y - rb._BODY_PAD_TOP))


def _bytes(surf):
    return pygame.image.tobytes(surf, "RGBA")


def _settle():
    platforms = build_stage()
    p1, p2, players = build_players()
    empty = InputFrame(set(), set(), set())
    for _ in range(10):
        for p in players:
            p.update(empty, platforms, pygame.sprite.Group())
    return p1, p2


def _compare(p):
    direct = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    direct.fill(BG_COLOR)
    _direct(direct, p)
    cached = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    cached.fill(BG_COLOR)
    _cached(cached, p)
    assert _bytes(direct) == _bytes(cached)


def test_body_cache_pixel_identical_both_players():
    p1, p2 = _settle()
    _compare(p1)
    _compare(p2)


def test_body_cache_pixel_identical_left_facing():
    p1, _ = _settle()
    p1.fighter.facing_right = False
    _compare(p1)


def test_body_cache_pixel_identical_hurt_tint():
    p1, _ = _settle()
    p1.fighter.hurt_timer = 1  # hurt flash -> body_tint(p) returns RED (#75)
    assert rb.body_tint(p1) == RED
    _compare(p1)
