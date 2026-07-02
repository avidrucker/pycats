"""Issue #4 — the tail must respond to gravity and collide with thick platforms.

Before the fix the tail stuck straight out / curled upward (tip ~21px ABOVE the
base) and had no platform awareness. After the fix each segment droops toward
straight-down (progressively toward the tip) and is pushed out of solid (thick)
platforms so it rests on the surface instead of clipping through. Thin platforms
remain pass-through.
"""
import pygame as pg
import pytest

from pycats.entities.player import Player
from pycats.entities.platform import Platform
from pycats.core.input import InputFrame
from pycats.config import P1_COLOR, WHITE
import pycats.entities.tail as _tail


@pytest.fixture(autouse=True)
def _physics_only(monkeypatch):
    # These tests verify the PHYSICS layer (gravity / collision / trailing). The
    # #42 curl/undulation are separate expression layers that re-pose the resting
    # tail; disable them here so the asserts isolate the physics rest pose.
    monkeypatch.setattr(_tail, "TAIL_CURL_STRENGTH", 0)

C = {"left": pg.K_a, "right": pg.K_d, "up": pg.K_w,
     "down": pg.K_s, "shield": pg.K_q, "attack": pg.K_e}


def _empty():
    return InputFrame(held=set(), pressed=set(), released=set())


def _player(y, platform):
    plats = pg.sprite.Group()
    plats.add(platform)
    p = Player(x=460, y=y, controls=C, color=P1_COLOR, eye_color=WHITE,
               char_name="Cat", facing_right=True)
    return p, plats


def test_tail_droops_under_gravity_on_ground():
    plat = Platform(pg.Rect(200, 400, 600, 20), thin=False)
    p, plats = _player(360, plat)
    empty = pg.sprite.Group()
    for _ in range(120):
        p.update(_empty(), plats, empty)
    base, tip = p.tail.segments[0], p.tail.segments[-1]
    assert tip.y - base.y > 3.0   # tip hangs BELOW the base (was ~-21 before)


def test_tail_trails_upward_while_falling():
    """#37 (Verlet model): in the air the tail has inertia, so while the cat is
    ACCELERATING downward the tail lags behind — its tip sits ABOVE the base
    (secondary motion / drag), rather than statically drooping below it. The
    stationary in-air hang is covered by test_tail_gravity_naturalness.py."""
    plat = Platform(pg.Rect(200, 560, 600, 20), thin=False)  # far below
    p, plats = _player(120, plat)
    empty = pg.sprite.Group()
    for _ in range(20):
        p.update(_empty(), plats, empty)  # falling
    base, tip = p.tail.segments[0], p.tail.segments[-1]
    assert tip.y < base.y          # trails UP behind the downward motion


def test_tail_rests_on_thick_platform_without_penetrating():
    plat = Platform(pg.Rect(200, 400, 600, 20), thin=False)
    p, plats = _player(360, plat)
    empty = pg.sprite.Group()
    for _ in range(120):
        p.update(_empty(), plats, empty)
    deepest = max(s.y - plat.rect.top for s in p.tail.segments)
    assert deepest <= 1.0         # no segment sinks below the solid top surface


def test_resolver_pushes_segment_out_of_thick_platform():
    plat = Platform(pg.Rect(200, 400, 600, 20), thin=False)
    p, plats = _player(360, plat)
    empty = pg.sprite.Group()
    p.update(_empty(), plats, empty)   # sets p.platforms
    seg = p.tail.segments[5]
    seg.x, seg.y = 460, plat.rect.top + 8   # 8px inside the solid platform
    p.tail._resolve_platform_collisions(plats)
    assert seg.y <= plat.rect.top + 0.001   # pushed up to the surface


def test_resolver_ignores_thin_platform():
    thin = Platform(pg.Rect(200, 400, 600, 20), thin=True)
    p, plats = _player(360, thin)
    empty = pg.sprite.Group()
    p.update(_empty(), plats, empty)
    seg = p.tail.segments[5]
    seg.x, seg.y = 460, thin.rect.top + 8    # inside a thin (pass-through) platform
    p.tail._resolve_platform_collisions(plats)
    assert seg.y == thin.rect.top + 8        # unchanged — tail passes through thin
