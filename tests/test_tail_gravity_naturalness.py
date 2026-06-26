"""Issue #37 — the gravity droop must be substantial and STABLE (not decay back
to horizontal), and a strong droop must not clip below a thick platform.

#4 added gravity but it was imperceptible: an angle nudge that the idle wave and
parent-following IK washed back out, peaking ~9px then decaying. #37 switches to
a positional sag (a persistent downward bias on each segment's IK target) and a
floor clamp that catches segments even when they overshoot past a thin platform.
"""
import math

import pygame as pg
import pytest

from pycats.entities.player import Player
from pycats.entities.platform import Platform
from pycats.core.input import InputFrame
from pycats.config import P1_COLOR, WHITE
import pycats.entities.tail as _tail


@pytest.fixture(autouse=True)
def _physics_only(monkeypatch):
    # Verify the PHYSICS layer (gravity hang); the #42 curl/undulation expression
    # layers re-pose the resting tail and are disabled here to isolate physics.
    monkeypatch.setattr(_tail, "TAIL_CURL_STRENGTH", 0)

C = {"left": pg.K_a, "right": pg.K_d, "up": pg.K_w,
     "down": pg.K_s, "shield": pg.K_q, "attack": pg.K_e}


def _empty():
    return InputFrame(held=set(), pressed=set(), released=set())


def test_gravity_droop_is_substantial_and_stable():
    """Pinned in open air, the tail hangs well below its base and stays there."""
    far = pg.sprite.Group()
    far.add(Platform(pg.Rect(0, 2000, 10, 10), thin=False))  # irrelevant
    p = Player(x=460, y=200, controls=C, color=P1_COLOR, eye_color=WHITE,
               char_name="Cat", facing_right=True)
    droop = {}
    for f in range(1, 401):
        p.rect.midbottom = (460, 300)   # pin so it settles without falling away
        p.vel.update(0, 0)
        p.update(_empty(), far, pg.sprite.Group())
        if f in (200, 400):
            base, tip = p.tail.segments[0], p.tail.segments[-1]
            droop[f] = tip.y - base.y
    assert droop[400] > 20.0                       # clearly hangs (was ~5 & decaying)
    assert abs(droop[400] - droop[200]) < 8.0      # stable, not decaying back up


def test_strong_droop_does_not_clip_below_thick_platform():
    """A segment that overshoots BELOW a (thin-tall) thick platform is clamped
    back to the top surface — the failure mode a push-out-if-inside test misses."""
    plat = Platform(pg.Rect(200, 400, 600, 20), thin=False)
    plats = pg.sprite.Group()
    plats.add(plat)
    p = Player(x=460, y=360, controls=C, color=P1_COLOR, eye_color=WHITE,
               char_name="Cat", facing_right=True)
    p.update(_empty(), plats, pg.sprite.Group())   # sets p.platforms
    seg = p.tail.segments[10]
    seg.x, seg.y = 460, plat.rect.bottom + 12       # 12px BELOW the whole platform
    p.tail._resolve_platform_collisions(plats)
    assert seg.y <= plat.rect.top + 0.001           # pulled back up onto the surface
