"""Weight-dependent set knockback (WDSK) — #211, a #142 combat gate.

Several PM moves (and the looping d-air) use *set* knockback: the launch is
independent of the victim's percent but still scales with the victim's weight.
SmashWiki "Knockback": set knockback replaces the damage `d` with the WDSK value
`s` and fixes the percent `p` at 10 — so it is exactly the normal formula called
with `percent=10, damage=s`.

A `Hitbox` may carry `set_knockback` (the WDSK value); None = normal percent
scaling (today's behavior). Opt-in, so goldens stay byte-identical.
"""
from types import SimpleNamespace

import math

import pygame
import pytest

from pycats.entities import Player
from pycats.entities.platform import Platform
from pycats.core.input import InputFrame
from pycats.combat.data import Circle, Hitbox
from pycats.combat.knockback import knockback, set_knockback

_CONTROLS = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w,
                 down=pygame.K_s, attack=pygame.K_v, special=pygame.K_c,
                 shield=pygame.K_x)


# ---------------------------------------------------------------- Cycle 1: schema

def test_hitbox_set_knockback_defaults_to_none():
    hb = Hitbox(circle=Circle(0, 0, 10), damage=3.0, angle=85)
    assert hb.set_knockback is None


def test_hitbox_accepts_set_knockback():
    hb = Hitbox(circle=Circle(0, 0, 10), damage=3.0, angle=85, set_knockback=55)
    assert hb.set_knockback == 55


# ---------------------------------------------------------- Cycle 2: pure formula

def test_set_knockback_equals_normal_formula_at_percent_10():
    """Set knockback IS the normal formula with percent fixed at 10 and damage =
    the WDSK value (SmashWiki)."""
    for s, w in [(55, 100), (40, 130), (30, 80)]:
        assert set_knockback(s, w, 0.0, 100.0) == knockback(10.0, s, w, 0.0, 100.0)


def test_set_knockback_is_weight_dependent():
    """A heavier victim takes less set knockback than a lighter one."""
    light = set_knockback(55, 80, 0.0, 100.0)
    heavy = set_knockback(55, 130, 0.0, 100.0)
    assert heavy < light


# ------------------------------------------------- Cycle 3: through receive_hit

def _mk():
    return Player(100, 100, _CONTROLS, (255, 160, 64), eye_color=(0, 0, 0),
                  char_name="P", facing_right=True)


def _atk(attacker, damage=3.0, bkb=0.0, kbg=100.0, angle=0, set_knockback=None):
    return SimpleNamespace(owner=attacker, damage=damage, base_knockback=bkb,
                           knockback_growth=kbg, angle=angle,
                           set_knockback=set_knockback)


def _struck_vx(set_knockback, victim_percent, weight=100):
    """Strike a defender directly; return the horizontal launch speed."""
    attacker = _mk()
    defender = _mk()
    defender.fighter.on_ground = False  # horizontal launch, no prone/landing path
    defender.fighter.weight = weight
    defender.fighter.percent = victim_percent
    defender.fighter.vel.x = 0.0
    defender.fighter.receive_hit(_atk(attacker, set_knockback=set_knockback))
    return defender.fighter.vel.x


def test_wdsk_launch_is_percent_independent():
    """A WDSK hit launches a 0% victim and a 100% victim identically (set)."""
    at0 = _struck_vx(set_knockback=55, victim_percent=0)
    at100 = _struck_vx(set_knockback=55, victim_percent=100)
    assert at0 > 0, "WDSK hit should still launch"
    assert at100 == pytest.approx(at0), "set knockback ignores the victim's percent"


def test_non_wdsk_hit_still_scales_with_percent():
    """A normal (set_knockback=None) hit launches a 100% victim FARTHER than a 0%
    one — the percent-scaling path is unchanged."""
    at0 = _struck_vx(set_knockback=None, victim_percent=0)
    at100 = _struck_vx(set_knockback=None, victim_percent=100)
    assert at100 > at0


def test_wdsk_launch_is_weight_dependent_through_receive_hit():
    """A heavier victim is launched less by the same WDSK hit."""
    light = _struck_vx(set_knockback=55, victim_percent=50, weight=80)
    heavy = _struck_vx(set_knockback=55, victim_percent=50, weight=130)
    assert heavy < light
