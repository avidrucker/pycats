"""Regression tests for the status-effect count-down bar (issue #111).

The bar shows how long a shield/stun lasts. Its data is a pure function,
``render_battle.status_bar_spec`` — fill ratio = remaining value over the known
constant max (so no per-instance start value is stored), seconds = whole seconds
left, honouring the ``SHOW_STATUS_TIMER_BARS`` toggle. A separate placement test
pins that the bar renders *above* the dizzy-star animation so the stars are
never covered.
"""

import os
import math
import types

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402
import pytest  # noqa: E402

from pycats import render_battle as rb  # noqa: E402
from pycats.config import (  # noqa: E402
    SHIELD_MAX_HP, SHIELD_BREAK_STUN_MAX, SHIELD_DRAIN_PER_FRAME, FPS,
    SHIELD_COLOR, YELLOW, EAR_HEIGHT,
)
from pycats.render_battle import DIZZY_ORBIT_LIFT  # noqa: E402


def _fake(state="idle", shield_hp=SHIELD_MAX_HP, stun_timer=0, cx=120, top=200):
    # status_bar_spec reads shield_hp/stun_timer through `.fighter` (#90); `state`
    # stays a direct Player attr. Self-ref so the flat stand-in satisfies both.
    ns = types.SimpleNamespace(
        state=state, shield_hp=shield_hp, stun_timer=stun_timer,
        rect=pygame.Rect(cx - 20, top, 40, 60),
    )
    ns.fighter = ns
    return ns


def test_no_status_returns_none():
    assert rb.status_bar_spec(_fake()) is None


def test_shield_ratio_and_seconds():
    p = _fake(state="shield", shield_hp=25)
    ratio, seconds, color = rb.status_bar_spec(p)
    assert ratio == 25 / SHIELD_MAX_HP
    # seconds to depletion at the hold-drain rate.
    assert seconds == math.ceil(25 / (SHIELD_DRAIN_PER_FRAME * FPS))
    assert color == SHIELD_COLOR


def test_stun_ratio_and_seconds():
    p = _fake(stun_timer=240)
    ratio, seconds, color = rb.status_bar_spec(p)
    # Fill is remaining-frames over the CONSTANT max — no stored initial value.
    assert ratio == 240 / SHIELD_BREAK_STUN_MAX
    assert seconds == math.ceil(240 / FPS)
    assert color == YELLOW


def test_shield_takes_precedence_over_stun():
    """A shielding fighter shows the shield bar even if stun_timer is nonzero."""
    p = _fake(state="shield", shield_hp=30, stun_timer=100)
    _, _, color = rb.status_bar_spec(p)
    assert color == SHIELD_COLOR


def test_toggle_off_suppresses_bar(monkeypatch):
    monkeypatch.setattr(rb, "SHOW_STATUS_TIMER_BARS", False)
    assert rb.status_bar_spec(_fake(stun_timer=200)) is None
    assert rb.status_bar_spec(_fake(state="shield", shield_hp=40)) is None


@pytest.mark.usefixtures("render_isolation")
def test_bar_renders_above_dizzy_stars(monkeypatch):
    """Every bar rect must sit above the dizzy-star orbit (stars never covered)."""
    p = _fake(stun_timer=300, top=200)
    star_center_y = p.rect.top - EAR_HEIGHT - DIZZY_ORBIT_LIFT

    captured = []
    real_rect = pygame.draw.rect

    def spy(surface, color, rect, *a, **k):
        captured.append(pygame.Rect(rect))
        return real_rect(surface, color, rect, *a, **k)

    monkeypatch.setattr(pygame.draw, "rect", spy)
    surf = pygame.Surface((400, 400))
    rb.draw_status_bar(surf, p, *rb.status_bar_spec(p))

    assert captured, "draw_status_bar drew no rects"
    # The whole bar (both rects) is above the star orbit centre, with the halo
    # gap to spare — i.e. its bottom edge clears the stars.
    for r in captured:
        assert r.bottom <= star_center_y - rb._STAR_HALO, (
            f"status bar rect {r} overlaps the dizzy stars at y={star_center_y}"
        )
