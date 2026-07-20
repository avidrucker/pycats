"""Ledge-grab INTANG bar renders during the hang (#658, revives #531).

#531 added a green INTANG timer bar for `ledge_intangible_timer` but gated it on
`state != "ledge_hang"` — the one state in which that timer is ever live — so it
never rendered in real play (the #531 dead-render defect). #658 drops that gate.
These tests drive an **actual** ledge grab (not only a synthetic fake) so the bar's
real render path is exercised. It stacks above the grabs-left dots (#657) — the #720
stack. Spec: docs/pm-reference/ledge-regrab-intangible-and-display.md.
"""

import pygame
import pytest

from pycats import config
from pycats import render_battle as rb
from pycats.core.input import InputFrame
from pycats.entities import Player
from pycats.entities.ledge import ledges_from_platforms
from pycats.entities.platform import Platform

_CONTROLS = dict(
    left=pygame.K_a,
    right=pygame.K_d,
    up=pygame.K_w,
    down=pygame.K_s,
    attack=pygame.K_v,
    special=pygame.K_c,
    shield=pygame.K_x,
)


def _player():
    return Player(200, 200, _CONTROLS, (255, 160, 64), eye_color=(0, 0, 0), char_name="P1", facing_right=True)


def _empty_frame():
    return InputFrame(held=set(), pressed=set(), released=set())


def _stage():
    return [Platform(pygame.Rect(80, 410, 800, 80), thin=False)]


def _grab_left(p, plats, ledges):
    p.rect.topleft = (80 - 40, 420)  # body just left of the left lip
    p.fighter.vel.x, p.fighter.vel.y = 0, 5  # descending
    p.fighter.on_ground = False
    p.update(_empty_frame(), plats, pygame.sprite.Group(), ledges)
    assert p.state == "ledge_hang"


@pytest.fixture(autouse=True)
def _bars_on(monkeypatch):
    monkeypatch.setattr(rb.runtime_settings, "show_status_timer_bars", lambda: True)


def test_intangible_bar_renders_during_a_real_hang():
    # Able-to-fail: with the old `state != "ledge_hang"` gate this returns [] while hanging.
    plats = _stage()
    ledges = ledges_from_platforms(plats)
    p = _player()
    _grab_left(p, plats, ledges)
    assert p.fighter.ledge_intangible_timer > 0  # burst live
    specs = rb.timer_bar_specs(p)
    intangible = [b for b in specs if b.label == "INTANG"]
    assert len(intangible) == 1  # exactly one INTANG bar (no duplicate from the dodge/getup source)
    assert intangible[0].color == rb.INTANGIBLE_BAR_COLOR


def test_intangible_bar_stacks_with_the_grabs_left_dots():
    # The #720 stack: during a hang both the INTANG bar (#658) and the grabs-left dots
    # (#657) show — neither suppresses the other.
    plats = _stage()
    ledges = ledges_from_platforms(plats)
    p = _player()
    _grab_left(p, plats, ledges)
    assert any(b.label == "INTANG" for b in rb.timer_bar_specs(p))
    assert rb.grabs_left_dots(p) == 5  # first grab -> 5 dots, live alongside the bar


def test_residual_bar_normalized_per_grant():
    # A 6th-grab (past-cutoff) residual: ledge_intangible_granted == the 5f residual, so the
    # bar drains a truthful 5/5 -> 0, same shape as any bar (the #720 normalized choice).
    residual = config.LEDGE_POST_CUTOFF_RESIDUAL_FRAMES
    plats = _stage()
    ledges = ledges_from_platforms(plats)
    p = _player()
    # synthesize the residual grant on a real hanging fighter (grant path is #656's;
    # driving 6 real regrabs is covered by test_ledge_regrab_cutoff).
    _grab_left(p, plats, ledges)
    p.fighter.ledge_intangible_timer = residual
    p.fighter.ledge_intangible_granted = residual
    (bar,) = [b for b in rb.timer_bar_specs(p) if b.label == "INTANG"]
    assert bar.ratio == 1.0  # full at the start of the residual window, not a proportional stub
