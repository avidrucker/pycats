"""Issue #42 — the curl/expression layer makes the resting tail hold a cat-like
curl on top of the passive Verlet physics.

With curl ON the resting tail lifts/curls (tip rises toward and above the base)
instead of hanging straight down; with curl OFF (strength 0) it falls back to the
pure-physics hang. This is the expression layer the physics tests disable.
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


def _settled_tip_dy(strength):
    """Tip y minus base y after settling, pinned in open air. Negative = curled up."""
    far = pg.sprite.Group()
    far.add(Platform(pg.Rect(0, 3000, 10, 10), thin=False))
    p = Player(x=460, y=200, controls=C, color=P1_COLOR, eye_color=WHITE,
               char_name="Cat", facing_right=True)
    for _ in range(300):
        p.rect.midbottom = (460, 300)
        p.vel.update(0, 0)
        p.update(_e(), far, pg.sprite.Group())
    base, tip = p.tail.segments[0], p.tail.segments[-1]
    return tip.y - base.y


def test_curl_on_lifts_the_tail(monkeypatch):
    # default curl strength is on; the resting tip should be lifted ABOVE the base
    dy = _settled_tip_dy(_tail.TAIL_CURL_STRENGTH)
    assert dy < 0          # curled up, not hanging down


def test_curl_off_falls_back_to_pure_hang(monkeypatch):
    monkeypatch.setattr(_tail, "TAIL_CURL_STRENGTH", 0)
    dy = _settled_tip_dy(0)
    assert dy > 20         # pure gravity hang: tip well below the base
