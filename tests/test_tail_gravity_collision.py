"""Issue #4 — the tail must respond to gravity and collide with thick platforms.

Before the fix the tail stuck straight out / curled upward (tip ~21px ABOVE the
base) and had no platform awareness. After the fix each segment droops toward
straight-down (progressively toward the tip) and is pushed out of solid (thick)
platforms so it rests on the surface instead of clipping through. Thin platforms
remain pass-through.
"""
import pygame as pg

from pycats.entities.player import Player
from pycats.entities.platform import Platform
from pycats.core.input import InputFrame
from pycats.config import P1_COLOR, WHITE

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


def test_tail_droops_under_gravity_in_air():
    plat = Platform(pg.Rect(200, 560, 600, 20), thin=False)  # far below
    p, plats = _player(120, plat)
    empty = pg.sprite.Group()
    for _ in range(20):
        p.update(_empty(), plats, empty)
    base, tip = p.tail.segments[0], p.tail.segments[-1]
    assert tip.y - base.y > 3.0


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
    p.tail._resolve_platform_collisions()
    assert seg.y <= plat.rect.top + 0.001   # pushed up to the surface


def test_resolver_ignores_thin_platform():
    thin = Platform(pg.Rect(200, 400, 600, 20), thin=True)
    p, plats = _player(360, thin)
    empty = pg.sprite.Group()
    p.update(_empty(), plats, empty)
    seg = p.tail.segments[5]
    seg.x, seg.y = 460, thin.rect.top + 8    # inside a thin (pass-through) platform
    p.tail._resolve_platform_collisions()
    assert seg.y == thin.rect.top + 8        # unchanged — tail passes through thin
