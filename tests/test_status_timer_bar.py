"""Regression tests for the shield/stun status bar (issue #111).

The bar shows how long a shield/stun lasts. Its data is a pure function,
``render_battle.timer_bar_specs`` (generalised from ``status_bar_spec`` in #340)
— fill ratio = remaining value over the known constant max (so no per-instance
start value is stored), seconds = whole seconds left, honouring the
``SHOW_STATUS_TIMER_BARS`` toggle. Slice 1 surfaces shield/stun as a single
unlabelled ``TimerBar``; the multi-bar/label/stacking behaviour is covered in
``test_timer_bars.py``. A separate placement test pins that the bar renders
*above* the dizzy-star animation so the stars are never covered.
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
    SHIELD_COLOR, YELLOW, EAR_HEIGHT, LEDGE_HANG_FRAMES, KNOCKDOWN_PRONE_FRAMES,
    LEDGE_REGRAB_LOCKOUT_FRAMES, DODGE_TIME, GETUP_ROLL_FRAMES,
)
from pycats.render_battle import DIZZY_ORBIT_LIFT  # noqa: E402


def _fake(state="idle", shield_hp=SHIELD_MAX_HP, stun_timer=0,
          ledge_hang_timer=0, prone_timer=0, ledge_regrab_lockout_timer=0,
          invulnerable=False, dodge_timer=0, getup_roll_timer=0,
          getup_attack_timer=0, cx=120, top=200):
    # timer_bar_specs reads the timers through `.fighter` (#90); `state` stays a
    # direct Player attr. Self-ref so the flat stand-in satisfies both.
    ns = types.SimpleNamespace(
        state=state, shield_hp=shield_hp, stun_timer=stun_timer,
        ledge_hang_timer=ledge_hang_timer, prone_timer=prone_timer,
        ledge_regrab_lockout_timer=ledge_regrab_lockout_timer,
        invulnerable=invulnerable, dodge_timer=dodge_timer,
        getup_roll_timer=getup_roll_timer, getup_attack_timer=getup_attack_timer,
        rect=pygame.Rect(cx - 20, top, 40, 60),
    )
    ns.fighter = ns
    return ns


def test_no_status_returns_empty():
    assert rb.timer_bar_specs(_fake()) == []


def test_shield_ratio_and_seconds():
    p = _fake(state="shield", shield_hp=25)
    (bar,) = rb.timer_bar_specs(p)
    assert bar.ratio == 25 / SHIELD_MAX_HP
    # seconds to depletion at the hold-drain rate.
    assert bar.readout == f"{math.ceil(25 / (SHIELD_DRAIN_PER_FRAME * FPS))}s"
    assert bar.color == SHIELD_COLOR
    assert bar.label is None   # unlabelled in slice 1 (byte-identity)


def test_stun_ratio_and_seconds():
    p = _fake(stun_timer=240)
    (bar,) = rb.timer_bar_specs(p)
    # Fill is remaining-frames over the CONSTANT max — no stored initial value.
    assert bar.ratio == 240 / SHIELD_BREAK_STUN_MAX
    assert bar.readout == f"{math.ceil(240 / FPS)}s"
    assert bar.color == YELLOW
    assert bar.label is None


def test_shield_takes_precedence_over_stun():
    """A shielding fighter shows the shield bar even if stun_timer is nonzero."""
    p = _fake(state="shield", shield_hp=30, stun_timer=100)
    (bar,) = rb.timer_bar_specs(p)
    assert bar.color == SHIELD_COLOR


def test_toggle_off_suppresses_bar(monkeypatch):
    # Toggle migrated from a config constant to the live runtime accessor (#121).
    monkeypatch.setattr(rb.runtime_settings, "show_status_timer_bars", lambda: False)
    assert rb.timer_bar_specs(_fake(stun_timer=200)) == []
    assert rb.timer_bar_specs(_fake(state="shield", shield_hp=40)) == []
    assert rb.timer_bar_specs(
        _fake(state="ledge_hang", ledge_hang_timer=90)) == []


# --- HANG bar (#348, slice 2 of #334) ----------------------------------------
# A teal count-down bar labelled HANG while a fighter clings to a ledge, draining
# as the ~2s ledge_hang_timer (#14) runs out.

def test_hang_bar_ratio_seconds_label_colour():
    p = _fake(state="ledge_hang", ledge_hang_timer=90)
    (bar,) = rb.timer_bar_specs(p)
    assert bar.label == "HANG"
    assert bar.color == rb.HANG_BAR_COLOR
    assert bar.ratio == 90 / LEDGE_HANG_FRAMES
    assert bar.readout == f"{math.ceil(90 / FPS)}s"


def test_no_hang_bar_when_not_hanging():
    # ledge_hang_timer 0 (or a non-hang state) shows no HANG bar.
    assert rb.timer_bar_specs(_fake(state="ledge_hang", ledge_hang_timer=0)) == []
    assert rb.timer_bar_specs(_fake(state="idle", ledge_hang_timer=90)) == []


def test_hang_bar_suppressed_by_toggle(monkeypatch):
    monkeypatch.setattr(rb.runtime_settings, "show_status_timer_bars", lambda: False)
    assert rb.timer_bar_specs(
        _fake(state="ledge_hang", ledge_hang_timer=90)) == []


# --- DOWN bar (#350, slice 3 of #334) ----------------------------------------
# An orange count-down bar labelled DOWN while a fighter is knocked down (prone,
# #13), draining as the ~0.5s getup window (prone_timer) runs out.

def test_down_bar_ratio_seconds_label_colour():
    p = _fake(state="prone", prone_timer=20)
    (bar,) = rb.timer_bar_specs(p)
    assert bar.label == "DOWN"
    assert bar.color == rb.DOWN_BAR_COLOR
    assert bar.ratio == 20 / KNOCKDOWN_PRONE_FRAMES
    assert bar.readout == f"{math.ceil(20 / FPS)}s"


def test_no_down_bar_when_not_prone():
    assert rb.timer_bar_specs(_fake(state="prone", prone_timer=0)) == []
    assert rb.timer_bar_specs(_fake(state="idle", prone_timer=20)) == []


def test_down_bar_suppressed_by_toggle(monkeypatch):
    monkeypatch.setattr(rb.runtime_settings, "show_status_timer_bars", lambda: False)
    assert rb.timer_bar_specs(_fake(state="prone", prone_timer=20)) == []


# --- LOCKOUT bar + multi-bar recency ordering (#357, slice 4 of #334) ---------
# LOCKOUT (post-drop regrab suppression, #14) is the first STATE-INDEPENDENT
# timer: it co-activates with the exclusive-state bars, so timer_bar_specs now
# returns a LIST ordered newest-on-top (least frames elapsed = nearest head).

def test_lockout_bar_ratio_seconds_label_colour():
    p = _fake(state="fall", ledge_regrab_lockout_timer=20)
    (bar,) = rb.timer_bar_specs(p)
    assert bar.label == "LOCKOUT"
    assert bar.color == rb.LOCKOUT_BAR_COLOR
    assert bar.ratio == 20 / LEDGE_REGRAB_LOCKOUT_FRAMES
    assert bar.readout == f"{math.ceil(20 / FPS)}s"


def test_no_lockout_bar_when_zero():
    assert rb.timer_bar_specs(_fake(state="fall", ledge_regrab_lockout_timer=0)) == []


def test_lockout_bar_suppressed_by_toggle(monkeypatch):
    monkeypatch.setattr(rb.runtime_settings, "show_status_timer_bars", lambda: False)
    assert rb.timer_bar_specs(
        _fake(state="fall", ledge_regrab_lockout_timer=20)) == []


def test_lockout_and_down_coactivate_ordered_by_recency():
    # LOCKOUT just started (elapsed 2), DOWN older (elapsed 25) -> LOCKOUT nearer
    # the head. Accumulation order is [DOWN, LOCKOUT], so [LOCKOUT, DOWN] proves
    # the recency SORT, not insertion order.
    p = _fake(state="prone", prone_timer=5,   # elapsed 25 of 30
              ledge_regrab_lockout_timer=28)  # elapsed 2 of 30
    labels = [b.label for b in rb.timer_bar_specs(p)]
    assert labels == ["LOCKOUT", "DOWN"]


def test_down_and_lockout_reverse_recency():
    # DOWN just started (elapsed 2), LOCKOUT older (elapsed 25) -> DOWN nearer head.
    p = _fake(state="prone", prone_timer=28,  # elapsed 2 of 30
              ledge_regrab_lockout_timer=5)   # elapsed 25 of 30
    labels = [b.label for b in rb.timer_bar_specs(p)]
    assert labels == ["DOWN", "LOCKOUT"]


def test_single_bar_cases_unchanged_by_recency_refactor():
    # Byte-identity guard: the exclusive-state single-bar cases still return
    # exactly one bar (the restructure must not change single-bar output).
    (shield,) = rb.timer_bar_specs(_fake(state="shield", shield_hp=25))
    assert shield.color == SHIELD_COLOR and shield.label is None
    (stun,) = rb.timer_bar_specs(_fake(stun_timer=240))
    assert stun.color == YELLOW and stun.label is None
    (hang,) = rb.timer_bar_specs(_fake(state="ledge_hang", ledge_hang_timer=90))
    assert hang.label == "HANG"
    (down,) = rb.timer_bar_specs(_fake(state="prone", prone_timer=20))
    assert down.label == "DOWN"


def test_shield_sorts_last_under_a_lockout_overlay():
    # A held shield (resource gauge, no frame elapsed) reads as background: a
    # co-active LOCKOUT count-down stacks above it (nearer the head).
    p = _fake(state="shield", shield_hp=40, ledge_regrab_lockout_timer=10)
    labels = [b.label for b in rb.timer_bar_specs(p)]
    assert labels == ["LOCKOUT", None]  # LOCKOUT nearest head, shield last


# --- INVULN bar (#358, slice 5 of #334; option 1 = per-source resolve) --------
# `invulnerable` is a bool driven by several actions, each with its own timer/max.
# The bar resolves the current source to (remaining, max); it is suppressed while
# ledge-hanging (HANG already shows that clock).

def test_invuln_bar_dodge_source():
    p = _fake(state="dodge", invulnerable=True, dodge_timer=10)
    (bar,) = rb.timer_bar_specs(p)
    assert bar.label == "INVULN"
    assert bar.color == rb.INVULN_BAR_COLOR
    assert bar.ratio == 10 / DODGE_TIME
    assert bar.readout == f"{math.ceil(10 / FPS)}s"


def test_invuln_bar_getup_roll_source():
    p = _fake(state="getup_roll", invulnerable=True, getup_roll_timer=8)
    (bar,) = rb.timer_bar_specs(p)
    assert bar.label == "INVULN"
    assert bar.ratio == 8 / GETUP_ROLL_FRAMES


def test_invuln_bar_getup_attack_source():
    p = _fake(state="getup_attack", invulnerable=True, getup_attack_timer=12)
    (bar,) = rb.timer_bar_specs(p)
    assert bar.label == "INVULN"
    assert bar.ratio == 12 / rb._GETUP_ATTACK_FRAMES


def test_no_invuln_bar_when_not_invulnerable():
    # The bool gates it: a lingering dodge_timer with invulnerable already cleared
    # shows no INVULN bar.
    assert rb.timer_bar_specs(
        _fake(state="dodge", invulnerable=False, dodge_timer=10)) == []


def test_invuln_suppressed_while_ledge_hanging():
    # Ledge-grab sets invulnerable=True, but HANG already shows that clock — only
    # the HANG bar renders, no redundant INVULN.
    p = _fake(state="ledge_hang", invulnerable=True, ledge_hang_timer=90)
    labels = [b.label for b in rb.timer_bar_specs(p)]
    assert labels == ["HANG"]


def test_invuln_bar_suppressed_by_toggle(monkeypatch):
    monkeypatch.setattr(rb.runtime_settings, "show_status_timer_bars", lambda: False)
    assert rb.timer_bar_specs(
        _fake(state="dodge", invulnerable=True, dodge_timer=10)) == []


def test_invuln_and_lockout_coactivate_ordered_by_recency():
    # Dodge INVULN just started (elapsed 4 of 14), LOCKOUT older (elapsed 25 of
    # 30) -> INVULN nearer the head.
    p = _fake(state="dodge", invulnerable=True, dodge_timer=10,  # elapsed 4
              ledge_regrab_lockout_timer=5)                      # elapsed 25
    labels = [b.label for b in rb.timer_bar_specs(p)]
    assert labels == ["INVULN", "LOCKOUT"]


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
    rb.draw_timer_bars(surf, p, rb.timer_bar_specs(p))

    assert captured, "draw_timer_bars drew no rects"
    # The whole bar (both rects) is above the star orbit centre, with the halo
    # gap to spare — i.e. its bottom edge clears the stars.
    for r in captured:
        assert r.bottom <= star_center_y - rb._STAR_HALO, (
            f"status bar rect {r} overlaps the dizzy stars at y={star_center_y}"
        )
