# tests/test_render_cache.py
"""The cat-body composite cache must be pixel-identical to drawing each frame."""
import pytest
import pygame

from pycats.config import BG_COLOR, SCREEN_WIDTH, SCREEN_HEIGHT, RED
from pycats.sim.runner import build_stage, build_players
from pycats.core.input import InputFrame
from pycats import render_battle as rb

# Re-init font + clear stale render/font caches before each test so a prior
# test's pygame.quit() can't break the pixel-identity assertions (#63).
pytestmark = pytest.mark.usefixtures("render_isolation")


def _direct(surface, p):
    """Replicate the original per-frame body draw sequence (pre-cache)."""
    body = pygame.Surface(p.rect.size)
    body.fill(rb.body_tint(p))  # tint is render-time now (#75), not p.image
    surface.blit(body, p.rect)
    rb.draw_stripes(surface, p)
    rb.draw_eye(surface, p)
    rb.draw_eye(surface, p, eye=False)
    rb.draw_cat_features(surface, p)
    rb.draw_player_name(surface, p)


def _cached(surface, p):
    body = rb._cat_body_surface(p)
    surface.blit(body, (p.rect.x - rb._BODY_PAD_X, p.rect.y - rb._BODY_PAD_TOP))


def _bytes(surf):
    return pygame.image.tobytes(surf, "RGBA")


def _settle():
    platforms = build_stage()
    p1, p2, players = build_players("legacy")
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
    p1.facing_right = False
    _compare(p1)


def test_body_cache_pixel_identical_hurt_tint():
    p1, _ = _settle()
    p1.hurt_timer = 1  # hurt flash -> body_tint(p) returns RED (#75)
    assert rb.body_tint(p1) == RED
    _compare(p1)
