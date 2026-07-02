"""Tests for the generalised above-head timer-bar drawer (issue #340, epic #334).

Slice 1 generalises the single #111 status bar into a *stacked, newest-on-top,
multi-spec* drawer: ``render_battle.timer_bar_specs`` returns an ordered list of
``TimerBar`` specs (colour + readout + optional label + fill ratio), and
``render_battle.draw_timer_bars`` stacks them above the fighter's head with
``specs[0]`` nearest the head.

These tests cover the NEW generalisation behaviour with *synthetic* specs
(stacking order, label present/absent, ratio clamp, and single-spec position
preservation — the byte-identity guard for shield/stun). The shield/stun *data*
regression stays in ``test_status_timer_bar.py``.
"""

import os
import types

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402
import pytest  # noqa: E402

from pycats import render_battle as rb  # noqa: E402
from pycats.config import EAR_HEIGHT  # noqa: E402
from pycats.render_battle import DIZZY_ORBIT_LIFT  # noqa: E402


def _fake(cx=120, top=200):
    return types.SimpleNamespace(rect=pygame.Rect(cx - 20, top, 40, 60))


def _bar(ratio=0.5, readout="3s", color=(10, 20, 30), label=None):
    return rb.TimerBar(ratio=ratio, readout=readout, color=color, label=label)


def _expected_base_bottom(p):
    """Replicate the #111 formula for the index-0 (nearest-head) bar bottom."""
    star_cy = p.rect.top - EAR_HEIGHT - DIZZY_ORBIT_LIFT
    return int(star_cy - rb._STAR_HALO - rb.STATUS_BAR_GAP_ABOVE_STARS)


def _bg_rects(monkeypatch, surf, p, specs):
    """Capture the background rects (full-width, so one per drawn bar)."""
    captured = []
    real_rect = pygame.draw.rect

    def spy(surface, color, rect, *a, **k):
        if color == rb.STATUS_BAR_BG:
            captured.append(pygame.Rect(rect))
        return real_rect(surface, color, rect, *a, **k)

    monkeypatch.setattr(pygame.draw, "rect", spy)
    rb.draw_timer_bars(surf, p, specs)
    return captured


@pytest.mark.usefixtures("render_isolation")
def test_single_spec_position_matches_111_formula(monkeypatch):
    """A single spec draws its background rect at the exact #111 bar position —
    the byte-identity guard for shield/stun."""
    p = _fake()
    surf = pygame.Surface((400, 400))
    rects = _bg_rects(monkeypatch, surf, p, [_bar()])
    assert len(rects) == 1
    r = rects[0]
    assert r.width == rb.STATUS_BAR_WIDTH
    assert r.height == rb.STATUS_BAR_HEIGHT
    assert r.left == p.rect.centerx - rb.STATUS_BAR_WIDTH // 2
    assert r.bottom == _expected_base_bottom(p)


@pytest.mark.usefixtures("render_isolation")
def test_specs_stack_newest_on_top(monkeypatch):
    """N specs stack at N distinct, non-overlapping rows; specs[0] nearest the
    head (lowest on screen = greatest y), each higher index further up."""
    p = _fake()
    surf = pygame.Surface((400, 400))
    rects = _bg_rects(monkeypatch, surf, p, [_bar(), _bar(), _bar()])
    assert len(rects) == 3
    bottoms = [r.bottom for r in rects]
    # index 0 nearest head (largest bottom), strictly decreasing upward.
    assert bottoms[0] > bottoms[1] > bottoms[2]
    # non-overlapping: each bar's bottom clears the next one's top.
    for lower, upper in zip(rects, rects[1:]):
        assert upper.bottom <= lower.top


@pytest.mark.usefixtures("render_isolation")
def test_label_rendered_when_present_absent_when_none(monkeypatch):
    """The label text is drawn iff the spec carries one (byte-identity for the
    label=None shield/stun case depends on this)."""
    p = _fake()
    surf = pygame.Surface((400, 400))
    calls = []
    monkeypatch.setattr(
        rb.text_utils, "render_text",
        lambda surface, text, *a, **k: calls.append(text),
    )
    rb.draw_timer_bars(surf, p, [_bar(readout="3s", label=None)])
    assert "3s" in calls and "HANG" not in calls

    calls.clear()
    rb.draw_timer_bars(surf, p, [_bar(readout="3s", label="HANG")])
    assert "3s" in calls and "HANG" in calls


@pytest.mark.usefixtures("render_isolation")
def test_ratio_clamped(monkeypatch):
    """Foreground fill never exceeds the bar width nor goes negative."""
    p = _fake()
    surf = pygame.Surface((400, 400))
    widths = []
    real_rect = pygame.draw.rect

    def spy(surface, color, rect, *a, **k):
        if color != rb.STATUS_BAR_BG:  # foreground fill rect
            widths.append(pygame.Rect(rect).width)
        return real_rect(surface, color, rect, *a, **k)

    monkeypatch.setattr(pygame.draw, "rect", spy)
    rb.draw_timer_bars(surf, p, [_bar(ratio=5.0)])   # over-full
    rb.draw_timer_bars(surf, p, [_bar(ratio=-2.0)])  # negative
    assert widths, "no foreground rect drawn for an over-full bar"
    assert all(0 <= w <= rb.STATUS_BAR_WIDTH for w in widths)


@pytest.mark.usefixtures("render_isolation")
def test_empty_specs_draws_nothing(monkeypatch):
    p = _fake()
    surf = pygame.Surface((400, 400))
    assert _bg_rects(monkeypatch, surf, p, []) == []
