"""Grabs-left dots above the head (#657) — visualise PM's 5-regrab ledge cutoff.

The dot count is a pure function of the shipped #656 counter, `render_battle.grabs_left_dots`:
each dot = one remaining grab (of LEDGE_REGRAB_INVULN_CUTOFF) that still grants the full
intangibility burst. Pinned to `ledge_regrab_count` (1 on the first grab): first grab → 5
dots, fifth → 1, sixth (past cutoff) → none; count 0 → none. Honours the status-bars toggle
and never suppresses (nor is suppressed by) the above-head timer bars. Spec:
docs/pm-reference/ledge-regrab-invuln-and-display.md. Harness mirrors test_status_timer_bar.py.
"""

import types

import pygame
import pytest

from pycats import render_battle as rb
from pycats.config import (
    LEDGE_REGRAB_INVULN_CUTOFF,
    LEDGE_REGRAB_LOCKOUT_FRAMES,
    SHIELD_MAX_HP,
)


def _fake(ledge_regrab_count=0, ledge_regrab_lockout_timer=0, state="idle", cx=120, top=200):
    # Self-ref stand-in: grabs_left_dots reads p.fighter.ledge_regrab_count; timer_bar_specs
    # reads the other timers through .fighter. One namespace satisfies both (as in #111 tests).
    ns = types.SimpleNamespace(
        state=state,
        ledge_regrab_count=ledge_regrab_count,
        shield_hp=SHIELD_MAX_HP,
        stun_timer=0,
        prone_timer=0,
        ledge_regrab_lockout_timer=ledge_regrab_lockout_timer,
        invulnerable=False,
        dodge_timer=0,
        getup_roll_timer=0,
        getup_attack_timer=0,
        smash_charge_timer=0,
        ledge_invuln_timer=0,
        ledge_invuln_granted=0,
        rect=pygame.Rect(cx - 20, top, 40, 60),
    )
    ns.fighter = ns
    return ns


@pytest.fixture(autouse=True)
def _bars_on(monkeypatch):
    # Deterministic: the dots share the status-bars toggle; force it ON (default) so a
    # polluted settings file can't flip these assertions.
    monkeypatch.setattr(rb.runtime_settings, "show_status_timer_bars", lambda: True)


# --- pure count: the pinned formula (able-to-fail) ---------------------------


def test_dots_decrement_across_the_five_grab_chain():
    # count 1..5 -> 5,4,3,2,1 dots (CUTOFF + 1 - count). First grab shows a full 5.
    expected = {1: 5, 2: 4, 3: 3, 4: 2, 5: 1}
    for count, dots in expected.items():
        assert rb.grabs_left_dots(_fake(ledge_regrab_count=count)) == dots


def test_no_dots_before_a_chain_or_past_the_cutoff():
    assert rb.grabs_left_dots(_fake(ledge_regrab_count=0)) == 0  # no chain / just reset
    assert rb.grabs_left_dots(_fake(ledge_regrab_count=LEDGE_REGRAB_INVULN_CUTOFF + 1)) == 0  # 6th, cut off
    assert rb.grabs_left_dots(_fake(ledge_regrab_count=9)) == 0  # deep past cutoff


def test_fifth_grab_is_one_dot_and_sixth_is_none():
    # The readability contract: 1 dot on the 5th (last invuln) grab, 0 on the 6th.
    assert rb.grabs_left_dots(_fake(ledge_regrab_count=5)) == 1
    assert rb.grabs_left_dots(_fake(ledge_regrab_count=6)) == 0


# --- toggle + stacking -------------------------------------------------------


def test_toggle_off_suppresses_the_dots(monkeypatch):
    monkeypatch.setattr(rb.runtime_settings, "show_status_timer_bars", lambda: False)
    assert rb.grabs_left_dots(_fake(ledge_regrab_count=1)) == 0


def test_dots_coexist_with_a_live_timer_bar():
    # A fighter still in a regrab chain (count 3) with the post-drop lockout bar live:
    # the dots and the bar must BOTH show — neither suppresses the other (#720 stack).
    p = _fake(ledge_regrab_count=3, ledge_regrab_lockout_timer=LEDGE_REGRAB_LOCKOUT_FRAMES)
    assert rb.grabs_left_dots(p) == 3
    assert len(rb.timer_bar_specs(p)) >= 1  # the LOCKOUT bar is still there


# --- draw path renders something --------------------------------------------

pytestmark = pytest.mark.usefixtures("render_isolation")


def test_draw_paints_dot_pixels():
    surface = pygame.Surface((240, 240))
    surface.fill((0, 0, 0))
    p = _fake(ledge_regrab_count=1, cx=120, top=120)  # 5 dots
    rb.draw_grabs_left_dots(surface, p, rb.grabs_left_dots(p))
    # Some green (GRABS_LEFT_DOT_COLOR) pixels must now exist where black was.
    green = rb.GRABS_LEFT_DOT_COLOR
    hits = sum(1 for x in range(0, 240, 2) for y in range(0, 240, 2) if tuple(surface.get_at((x, y)))[:3] == green)
    assert hits > 0


def test_draw_is_noop_for_zero_dots():
    surface = pygame.Surface((240, 240))
    surface.fill((7, 7, 7))
    rb.draw_grabs_left_dots(surface, _fake(ledge_regrab_count=0), 0)
    assert tuple(surface.get_at((120, 120)))[:3] == (7, 7, 7)  # untouched
