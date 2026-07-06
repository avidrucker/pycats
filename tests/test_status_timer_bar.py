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

import math
import os
import types

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402
import pytest  # noqa: E402

from pycats import render_battle as rb  # noqa: E402
from pycats.config import (  # noqa: E402
    DODGE_TIME,
    EAR_HEIGHT,
    FPS,
    GETUP_ROLL_FRAMES,
    KNOCKDOWN_PRONE_FRAMES,
    LEDGE_REGRAB_LOCKOUT_FRAMES,
    SHIELD_BREAK_STUN_MAX,
    SHIELD_DRAIN_PER_FRAME,
    SHIELD_MAX_HP,
    SMASH_CHARGE_FRAMES,
)
from pycats.render_battle import DIZZY_ORBIT_LIFT  # noqa: E402


def _fake(
    state="idle",
    shield_hp=SHIELD_MAX_HP,
    stun_timer=0,
    prone_timer=0,
    ledge_regrab_lockout_timer=0,
    invulnerable=False,
    dodge_timer=0,
    getup_roll_timer=0,
    getup_attack_timer=0,
    smash_charge_timer=0,
    cx=120,
    top=200,
):
    # timer_bar_specs reads the timers through `.fighter` (#90); `state` stays a
    # direct Player attr. Self-ref so the flat stand-in satisfies both.
    ns = types.SimpleNamespace(
        state=state,
        shield_hp=shield_hp,
        stun_timer=stun_timer,
        prone_timer=prone_timer,
        ledge_regrab_lockout_timer=ledge_regrab_lockout_timer,
        invulnerable=invulnerable,
        dodge_timer=dodge_timer,
        getup_roll_timer=getup_roll_timer,
        getup_attack_timer=getup_attack_timer,
        smash_charge_timer=smash_charge_timer,
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
    assert bar.color == rb.SHIELD_BAR_COLOR  # blue bar hue (#364), != shield bubble
    assert bar.label == "SHIELD"


def test_stun_ratio_and_seconds():
    p = _fake(stun_timer=240)
    (bar,) = rb.timer_bar_specs(p)
    # Fill is remaining-frames over the CONSTANT max — no stored initial value.
    assert bar.ratio == 240 / SHIELD_BREAK_STUN_MAX
    assert bar.readout == f"{math.ceil(240 / FPS)}s"
    assert bar.color == rb.DIZZY_BAR_COLOR  # magenta bar hue (#364), != dizzy stars
    assert bar.label == "DIZZY"


def test_shield_takes_precedence_over_stun():
    """A shielding fighter shows the shield bar even if stun_timer is nonzero."""
    p = _fake(state="shield", shield_hp=30, stun_timer=100)
    (bar,) = rb.timer_bar_specs(p)
    assert bar.color == rb.SHIELD_BAR_COLOR
    assert bar.label == "SHIELD"


def test_toggle_off_suppresses_bar(monkeypatch):
    # Toggle migrated from a config constant to the live runtime accessor (#121).
    monkeypatch.setattr(rb.runtime_settings, "show_status_timer_bars", lambda: False)
    assert rb.timer_bar_specs(_fake(stun_timer=200)) == []
    assert rb.timer_bar_specs(_fake(state="shield", shield_hp=40)) == []


# --- HANG bar removed (#475) --------------------------------------------------
# The teal HANG count-down bar tracked the ledge-hang timeout; #475 removed that
# timeout (PM has no hang timer), so the bar and its HANG_BAR_COLOR are gone. A
# ledge-hang state now shows no HANG bar; the ledge intangibility burst gets its
# own bar in the follow-up #531.


def test_no_hang_bar_while_ledge_hanging():
    assert rb.timer_bar_specs(_fake(state="ledge_hang")) == []


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
    assert rb.timer_bar_specs(_fake(state="fall", ledge_regrab_lockout_timer=20)) == []


def test_lockout_and_down_coactivate_ordered_by_recency():
    # LOCKOUT just started (elapsed 2), DOWN older (elapsed 25) -> LOCKOUT nearer
    # the head. Accumulation order is [DOWN, LOCKOUT], so [LOCKOUT, DOWN] proves
    # the recency SORT, not insertion order.
    p = _fake(
        state="prone",
        prone_timer=5,  # elapsed 25 of 30
        ledge_regrab_lockout_timer=28,
    )  # elapsed 2 of 30
    labels = [b.label for b in rb.timer_bar_specs(p)]
    assert labels == ["LOCKOUT", "DOWN"]


def test_down_and_lockout_reverse_recency():
    # DOWN just started (elapsed 2), LOCKOUT older (elapsed 25) -> DOWN nearer head.
    p = _fake(
        state="prone",
        prone_timer=28,  # elapsed 2 of 30
        ledge_regrab_lockout_timer=5,
    )  # elapsed 25 of 30
    labels = [b.label for b in rb.timer_bar_specs(p)]
    assert labels == ["DOWN", "LOCKOUT"]


def test_single_bar_cases_each_return_one_labelled_bar():
    # Each exclusive-state case returns exactly one bar with its spec label.
    (shield,) = rb.timer_bar_specs(_fake(state="shield", shield_hp=25))
    assert shield.color == rb.SHIELD_BAR_COLOR and shield.label == "SHIELD"
    (stun,) = rb.timer_bar_specs(_fake(stun_timer=240))
    assert stun.color == rb.DIZZY_BAR_COLOR and stun.label == "DIZZY"
    (down,) = rb.timer_bar_specs(_fake(state="prone", prone_timer=20))
    assert down.label == "DOWN"


def test_shield_sorts_last_under_a_lockout_overlay():
    # A held shield (resource gauge, no frame elapsed) reads as background: a
    # co-active LOCKOUT count-down stacks above it (nearer the head).
    p = _fake(state="shield", shield_hp=40, ledge_regrab_lockout_timer=10)
    labels = [b.label for b in rb.timer_bar_specs(p)]
    assert labels == ["LOCKOUT", "SHIELD"]  # LOCKOUT nearest head, shield last


# --- INVULN bar (#358, slice 5 of #334; option 1 = per-source resolve) --------
# `invulnerable` is a bool driven by several actions, each with its own timer/max.
# The bar resolves the current source to (remaining, max); it is suppressed while
# ledge-hanging (the dedicated ledge-invuln bar is #531; #475 removed the old HANG).


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
    assert rb.timer_bar_specs(_fake(state="dodge", invulnerable=False, dodge_timer=10)) == []


def test_invuln_suppressed_while_ledge_hanging():
    # Ledge-grab sets invulnerable=True, but the INVULN bar stays suppressed during
    # ledge_hang: no bar renders while hanging (#475 removed HANG; the dedicated
    # ledge-invuln bar is the follow-up #531). Able-to-fail if the suppression drops.
    p = _fake(state="ledge_hang", invulnerable=True)
    labels = [b.label for b in rb.timer_bar_specs(p)]
    assert labels == []


def test_invuln_bar_suppressed_by_toggle(monkeypatch):
    monkeypatch.setattr(rb.runtime_settings, "show_status_timer_bars", lambda: False)
    assert rb.timer_bar_specs(_fake(state="dodge", invulnerable=True, dodge_timer=10)) == []


def test_invuln_and_lockout_coactivate_ordered_by_recency():
    # Dodge INVULN just started (elapsed 4 of 14), LOCKOUT older (elapsed 25 of
    # 30) -> INVULN nearer the head.
    p = _fake(
        state="dodge",
        invulnerable=True,
        dodge_timer=10,  # elapsed 4
        ledge_regrab_lockout_timer=5,
    )  # elapsed 25
    labels = [b.label for b in rb.timer_bar_specs(p)]
    assert labels == ["INVULN", "LOCKOUT"]


# --- CHARGE bar (#380, final slice of #334) — the one FILL bar -----------------
# Grows 0->100% as smash_charge_timer accumulates (#371); readout = %-and-
# seconds-to-full; holds at 100% when maxed.


def test_charge_bar_fills_and_reads_percent_and_seconds():
    p = _fake(state="smash_charge", smash_charge_timer=30)  # ~half of the 59f ramp (#599)
    (bar,) = rb.timer_bar_specs(p)
    assert bar.label == "CHARGE"
    assert bar.color == rb.CHARGE_BAR_COLOR
    assert bar.ratio == 30 / SMASH_CHARGE_FRAMES  # fills UP
    # Concrete literal, NOT derived from SMASH_CHARGE_FRAMES, so this test itself reds
    # on a wrong ramp (#627 — was tautological/Free-Ride when the expected was computed
    # from the code's own constant). At timer=30 over the PM 59f ramp:
    # round(30/59*100) = 51%, ceil((59-30)/60) = 1s. Revert-check: set the ramp to 60
    # and the readout becomes "50%·1s", flipping this assertion red.
    assert bar.readout == "51%·1s"


def test_charge_bar_holds_at_full():
    p = _fake(state="smash_charge", smash_charge_timer=SMASH_CHARGE_FRAMES)
    (bar,) = rb.timer_bar_specs(p)
    assert bar.ratio == 1.0
    assert bar.readout == "100%·0s"  # holds at 100%, 0s to full


def test_no_charge_bar_when_not_charging():
    assert rb.timer_bar_specs(_fake(smash_charge_timer=0)) == []


def test_charge_bar_suppressed_by_toggle(monkeypatch):
    monkeypatch.setattr(rb.runtime_settings, "show_status_timer_bars", lambda: False)
    assert rb.timer_bar_specs(_fake(state="smash_charge", smash_charge_timer=30)) == []


def test_charge_and_lockout_coactivate_ordered_by_recency():
    # CHARGE just started (elapsed 3), LOCKOUT older (elapsed 25 of 30) -> CHARGE
    # nearer the head. Proves the fill bar's up-count joins the recency sort.
    p = _fake(
        state="smash_charge",
        smash_charge_timer=3,  # elapsed 3
        ledge_regrab_lockout_timer=5,
    )  # elapsed 25
    labels = [b.label for b in rb.timer_bar_specs(p)]
    assert labels == ["CHARGE", "LOCKOUT"]


# --- RECHARGE bar (#597) — shield HP regenerating after release ---------------
# A teal FILL bar shown ONLY while the shield is recharging (not shielding, HP
# below full, and NOT during shield-break dizzy). Fills 0->100% as shield_hp
# climbs; readout = whole seconds to full. Never co-renders with DIZZY.


def test_recharge_bar_fills_and_reads_seconds_to_full():
    p = _fake(state="idle", shield_hp=20)  # released, regenerating toward full
    (bar,) = rb.timer_bar_specs(p)
    assert bar.label == "RECHARGE"
    assert bar.color == rb.RECHARGE_BAR_COLOR
    assert bar.ratio == 20 / SHIELD_MAX_HP  # fills UP toward full
    frames_to_full = (SHIELD_MAX_HP - 20) / SHIELD_DRAIN_PER_FRAME
    assert bar.readout == f"{math.ceil(frames_to_full / FPS)}s"  # seconds to 100%


def test_no_recharge_bar_when_shield_full():
    # At full HP there is nothing to recharge — no bar.
    assert rb.timer_bar_specs(_fake(state="idle", shield_hp=SHIELD_MAX_HP)) == []


def test_no_recharge_bar_while_shielding():
    # Actively shielding drains, so it shows the SHIELD bar, never RECHARGE.
    labels = [b.label for b in rb.timer_bar_specs(_fake(state="shield", shield_hp=20))]
    assert labels == ["SHIELD"]


def test_recharge_never_coexists_with_dizzy():
    # A shield that broke -> dizzy stun with HP below full: only DIZZY shows. The
    # `stun_timer == 0` clause makes the mutual exclusion structural, not incidental.
    # Able-to-fail: drop that clause and RECHARGE joins DIZZY here.
    p = _fake(state="idle", shield_hp=0, stun_timer=240)
    labels = [b.label for b in rb.timer_bar_specs(p)]
    assert "DIZZY" in labels
    assert "RECHARGE" not in labels


def test_recharge_shows_climbing_from_empty_after_stun_ends():
    # Once the dizzy stun clears (stun_timer == 0) the shield is still at 0 and
    # regenerating -> RECHARGE now shows, filling from empty (ratio 0.0). This is
    # the intended post-stun behaviour; only the overlap-with-stun window is hidden.
    p = _fake(state="idle", shield_hp=0, stun_timer=0)
    (bar,) = rb.timer_bar_specs(p)
    assert bar.label == "RECHARGE"
    assert bar.ratio == 0.0


def test_recharge_bar_suppressed_by_toggle(monkeypatch):
    monkeypatch.setattr(rb.runtime_settings, "show_status_timer_bars", lambda: False)
    assert rb.timer_bar_specs(_fake(state="idle", shield_hp=20)) == []


def test_recharge_sorts_last_under_a_lockout_overlay():
    # A regenerating shield reads as background (like the drain gauge): a co-active
    # LOCKOUT count-down stacks above it (nearer the head).
    p = _fake(state="fall", shield_hp=20, ledge_regrab_lockout_timer=10)
    labels = [b.label for b in rb.timer_bar_specs(p)]
    assert labels == ["LOCKOUT", "RECHARGE"]  # LOCKOUT nearest head, recharge last


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
