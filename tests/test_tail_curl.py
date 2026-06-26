"""Issue #42 — the tail's EXPRESSION layer: a cat-like curl plus a continuous
undulation, both on top of the passive Verlet physics.

- curl lifts/curls the resting tail (tip rises toward/above the base) vs the
  pure-physics hang.
- undulation makes the tail snake/flow continuously even when idle (the tip and
  body keep moving frame to frame).

Both are gated by TAIL_CURL_STRENGTH (0 = pure passive physics), which is why the
physics tests disable this layer.
"""
import pygame as pg
import pytest

from pycats.entities.player import Player
from pycats.entities.platform import Platform
from pycats.core.input import InputFrame
from pycats.config import P1_COLOR, WHITE
import pycats.entities.tail as _tail

C = {"left": pg.K_a, "right": pg.K_d, "up": pg.K_w,
     "down": pg.K_s, "shield": pg.K_q, "attack": pg.K_e}


def _e():
    return InputFrame(held=set(), pressed=set(), released=set())


def _pinned_player():
    far = pg.sprite.Group()
    far.add(Platform(pg.Rect(0, 3000, 10, 10), thin=False))
    p = Player(x=460, y=200, controls=C, color=P1_COLOR, eye_color=WHITE,
               char_name="Cat", facing_right=True)
    return p, far


def test_curl_on_lifts_the_tail(monkeypatch):
    # isolate the curl: no undulation, so the settled pose is stable
    monkeypatch.setattr(_tail, "TAIL_UNDULATE_AMP", 0.0)
    p, far = _pinned_player()
    for _ in range(300):
        p.rect.midbottom = (460, 300)
        p.fighter.vel.update(0, 0)
        p.update(_e(), far, pg.sprite.Group())
    base, tip = p.tail.segments[0], p.tail.segments[-1]
    assert tip.y - base.y < 0          # curled up, not hanging down


def test_curl_off_falls_back_to_pure_hang(monkeypatch):
    monkeypatch.setattr(_tail, "TAIL_CURL_STRENGTH", 0)   # disables whole layer
    p, far = _pinned_player()
    for _ in range(300):
        p.rect.midbottom = (460, 300)
        p.fighter.vel.update(0, 0)
        p.update(_e(), far, pg.sprite.Group())
    base, tip = p.tail.segments[0], p.tail.segments[-1]
    assert tip.y - base.y > 20         # pure gravity hang: tip well below base


def test_undulation_keeps_the_idle_tail_moving():
    # defaults (undulation on): a pinned, otherwise-idle tail keeps snaking.
    p, far = _pinned_player()
    for _ in range(200):               # reach steady undulation
        p.rect.midbottom = (460, 300)
        p.fighter.vel.update(0, 0)
        p.update(_e(), far, pg.sprite.Group())
    xs = []
    for _ in range(120):               # ~2s
        p.rect.midbottom = (460, 300)
        p.fighter.vel.update(0, 0)
        p.update(_e(), far, pg.sprite.Group())
        xs.append(p.tail.segments[-1].x)
    # tip keeps travelling a continuous lateral range (well above the disabled
    # ~0 baseline below); exact magnitude is a tunable feel value.
    assert max(xs) - min(xs) > 2.0


def test_no_undulation_when_disabled(monkeypatch):
    monkeypatch.setattr(_tail, "TAIL_UNDULATE_AMP", 0.0)
    p, far = _pinned_player()
    for _ in range(200):
        p.rect.midbottom = (460, 300)
        p.fighter.vel.update(0, 0)
        p.update(_e(), far, pg.sprite.Group())
    xs = []
    for _ in range(120):
        p.rect.midbottom = (460, 300)
        p.fighter.vel.update(0, 0)
        p.update(_e(), far, pg.sprite.Group())
        xs.append(p.tail.segments[-1].x)
    assert max(xs) - min(xs) < 1.0     # settled, no continuous motion
