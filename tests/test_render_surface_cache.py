# tests/test_render_surface_cache.py
"""Per-frame surface reuse in render_battle (#1266).

`render_battle` / `render_attacks` used to rebuild three kinds of short-lived
surface every frame — the crouch/breath-rescaled body layers, the shield bubble,
and the attack hitbox visual — defeating the body-layer cache and pressuring GC
(measured ~30ms self-time, #1247 hotspot B2). These caches key each surface by
the inputs that determine its pixels, so a steady state reuses one surface.

Each cache test is able-to-fail: it asserts the *second* identical frame does not
reallocate, which reds against the pre-cache "rebuild every frame" code. Parity
tests assert the cached surface is byte-identical to a fresh build.
"""

import pygame
import pytest

from pycats import render_battle as rb
from pycats.config import (
    MAX_SHIELD_RADIUS,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SHIELD_COLOR,
    SHIELD_MAX_HP,
)
from pycats.core.input import InputFrame
from pycats.sim.runner import build_players, build_stage
from pycats.ui import cat_faces

pytestmark = pytest.mark.usefixtures("render_isolation")


def _bytes(surf):
    return pygame.image.tobytes(surf, "RGBA")


def _settle():
    """Advance both players a few frames so rects/tails are valid, then return P1."""
    platforms = build_stage()
    p1, p2, players = build_players()
    empty = InputFrame(set(), set(), set())
    for _ in range(10):
        for p in players:
            p.update(empty, platforms, pygame.sprite.Group())
    return p1, p2, players, platforms


def _frame():
    return pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))


def _force_state(monkeypatch, p, label):
    """Pin p.state (engine-derived, no setter) to `label` for the render-only test."""
    monkeypatch.setattr(type(p), "state", property(lambda self: label))


# --- scaled body layers (crouch / breath) ------------------------------------


def test_settled_crouch_frame_does_not_rescale_twice(monkeypatch):
    """A crouch that has finished easing scales the body to the same size every
    frame — the second such frame must hit the scaled-layer cache and call no
    pygame.transform.scale. Able-to-fail: reds against per-frame rescaling."""
    p1, _p2, players, platforms = _settle()
    _force_state(monkeypatch, p1, "crouch")
    p1._crouch_anim = 1.0  # fully settled -> constant scale factor
    surf = _frame()
    rb.render_battle(surf, [p1], platforms)  # warm the scaled-layer cache

    calls = []
    real_scale = pygame.transform.scale
    monkeypatch.setattr(pygame.transform, "scale", lambda s, sz: calls.append(sz) or real_scale(s, sz))
    rb.render_battle(surf, [p1], platforms)
    assert calls == [], f"settled crouch reallocated scaled layers: {calls}"


def test_scaled_layers_cache_pixel_identical():
    """The cached scaled ring/body are byte-identical to a fresh transform.scale."""
    p1, _p2, _players, _platforms = _settle()
    face = getattr(p1, "face_style", cat_faces.PRIMITIVES)  # as render_battle resolves it
    ring, body = rb._cat_body_layers(p1, face)
    size = (ring.get_width(), max(1, ring.get_height() - 7))
    fresh_ring = pygame.transform.scale(ring, size)
    fresh_body = pygame.transform.scale(body, size)
    cached_ring, cached_body = rb._cat_body_layers_scaled(p1, face, size)
    assert _bytes(cached_ring) == _bytes(fresh_ring)
    assert _bytes(cached_body) == _bytes(fresh_body)


# --- shield bubble ------------------------------------------------------------


def test_steady_shield_frame_does_not_rebuild_bubble(monkeypatch):
    """A shielding fighter whose shield_hp is unchanged draws the same-radius
    bubble every frame — the second frame must reuse the cached surface and build
    no new one. Able-to-fail: reds against per-frame Surface allocation."""
    p1, _p2, _players, platforms = _settle()
    _force_state(monkeypatch, p1, "shield")
    p1.fighter.shield_hp = SHIELD_MAX_HP
    surf = _frame()
    rb.render_battle(surf, [p1], platforms)  # warm the bubble cache

    built = []
    real_surface = pygame.Surface
    monkeypatch.setattr(pygame, "Surface", lambda *a, **k: built.append(a[0] if a else None) or real_surface(*a, **k))
    rb.render_battle(surf, [p1], platforms)
    r = MAX_SHIELD_RADIUS  # full hp -> full radius
    assert (r * 2, r * 2) not in built, f"steady shield rebuilt the bubble: {built}"


def test_shield_bubble_pixel_identical():
    """The cached bubble is byte-identical to a fresh SRCALPHA circle build."""
    r = MAX_SHIELD_RADIUS
    fresh = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
    pygame.draw.circle(fresh, (*SHIELD_COLOR, rb.SHIELD_FILL_ALPHA), (r, r), r)
    assert _bytes(rb._shield_bubble(r)) == _bytes(fresh)


# --- attack hitbox visual -----------------------------------------------------


def test_moving_attack_reuses_surface_across_frames(monkeypatch):
    """A rigid attack shifted by whole pixels keeps the same local circle layout,
    so its visual surface is rebuilt once and reused. Able-to-fail: reds against
    per-frame _attack_surface allocation."""
    p1, _p2, _players, platforms = _settle()

    class _Rect:
        def __init__(self, x, y, w, h):
            self.x, self.y, self.w, self.h = x, y, w, h

        @property
        def size(self):
            return (self.w, self.h)

        @property
        def topleft(self):
            return (self.x, self.y)

    class _Attack:
        def __init__(self, x, y):
            self.rect = _Rect(x, y, 30, 30)
            # two circles, positions relative to rect.topleft are constant as it moves
            self.resolved = [(x + 8, y + 8, 6, None), (x + 20, y + 18, 5, None)]

    surf = _frame()
    rb.render_attacks(surf, [_Attack(100, 100)])  # warm

    calls = []
    real_surface = pygame.Surface
    monkeypatch.setattr(pygame, "Surface", lambda *a, **k: calls.append(a) or real_surface(*a, **k))
    rb.render_attacks(surf, [_Attack(140, 100)])  # same shape, shifted +40px
    assert calls == [], f"moving attack rebuilt its surface: {calls}"


def test_attack_surface_cache_pixel_identical():
    """The cached attack surface equals a fresh per-frame build."""

    class _Rect:
        def __init__(self, x, y, w, h):
            self.x, self.y, self.w, self.h = x, y, w, h

        @property
        def size(self):
            return (self.w, self.h)

        @property
        def topleft(self):
            return (self.x, self.y)

    class _Attack:
        def __init__(self):
            self.rect = _Rect(50, 60, 30, 30)
            self.resolved = [(58, 68, 6, None), (70, 78, 5, None)]

    a = _Attack()
    cached = rb._attack_surface(a)
    fresh = rb._build_attack_surface(a)
    assert _bytes(cached) == _bytes(fresh)
