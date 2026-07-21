"""tests/test_tangibility.py

The 3-way immunity state `Tangibility` and its most-protective resolver (#802,
decision #784).

A fighter's per-frame tangibility is the MOST-PROTECTIVE of its active immunity
signals, precedence **INTANGIBLE > INVINCIBLE > TANGIBLE**. Grounded in the #797
findings (docs/research/2026-07-20-pm-invincible-hitlag-findings.md, §Q4-bonus):
meleelight `hurtBoxStateUpdate` evaluates the intangible check AFTER the invincible
one, so a fighter with both timers live resolves to intangible (pass-through wins).
The PM-3.6 step is `[inference]` — no PM primary exists; strongest source is the
meleelight Melee-engine reimpl + series-universal SmashWiki, PM-codeset carries no
override.
"""

import pygame

from pycats.combat.tangibility import Tangibility, resolve_tangibility
from pycats.entities.player import Player

P1 = dict(
    left=pygame.K_a,
    right=pygame.K_d,
    up=pygame.K_w,
    down=pygame.K_s,
    attack=pygame.K_v,
    special=pygame.K_c,
    shield=pygame.K_x,
)


def _mk():
    return Player(100, 100, P1, (255, 160, 64), eye_color=(0, 0, 0), char_name="P1", facing_right=True)


# ---- the enum -------------------------------------------------------------


def test_exactly_three_states():
    assert {t.name for t in Tangibility} == {"TANGIBLE", "INTANGIBLE", "INVINCIBLE"}


# ---- the pure resolver ----------------------------------------------------


def test_resolve_default_is_tangible():
    assert resolve_tangibility(intangible=False, invincible=False) is Tangibility.TANGIBLE


def test_resolve_intangible():
    assert resolve_tangibility(intangible=True, invincible=False) is Tangibility.INTANGIBLE


def test_resolve_invincible():
    assert resolve_tangibility(intangible=False, invincible=True) is Tangibility.INVINCIBLE


def test_most_protective_wins_intangible_over_invincible():
    # Tie-break (#802 acceptance / #784 precedence, #797 §Q4-bonus): both live -> INTANGIBLE.
    assert resolve_tangibility(intangible=True, invincible=True) is Tangibility.INTANGIBLE


# ---- the Fighter property (derived from the imperative signals) -----------


def test_fighter_property_tangible_by_default():
    pygame.init()
    assert _mk().fighter.tangibility is Tangibility.TANGIBLE


def test_fighter_property_intangible_when_intangible_set():
    pygame.init()
    p = _mk()
    p.fighter.intangible = True
    assert p.fighter.tangibility is Tangibility.INTANGIBLE


def test_fighter_property_invincible_when_timer_live():
    pygame.init()
    p = _mk()
    p.fighter.invincible_timer = 30
    assert p.fighter.tangibility is Tangibility.INVINCIBLE


def test_fighter_property_both_timers_resolve_intangible():
    # A fighter whose intangible AND invincible signals are both active -> INTANGIBLE.
    pygame.init()
    p = _mk()
    p.fighter.intangible = True
    p.fighter.invincible_timer = 30
    assert p.fighter.tangibility is Tangibility.INTANGIBLE
