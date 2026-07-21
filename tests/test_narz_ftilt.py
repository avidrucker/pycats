"""Narz forward-tilt — the disjoint+tipper identity move (slice 2 of #294, #299).

Pins the two PM-Marth signature mechanics, both pure data on the current engine (#290):
- **Tipper:** when a defender overlaps BOTH boxes, the TIP (box 0) wins — priority is
  tuple order (`entities/attack.py:36`; `systems/combat.py:141`). Able-to-fail: swap the
  tuple order or equalize the boxes and the tip-damage assertion fails.
- **Disjoint reach:** the tip hitbox sits beyond Narz's hurtbox.

Harness mirrors tests/test_multi_hitbox.py (process_hits + lightweight player stubs).
"""
from __future__ import annotations

import types

import pygame

from pycats.characters.narz_cat import _NARZ_FTILT
from pycats.combat.data import Circle, FighterData, Hurtbox, load_fighter_data
from pycats.entities.attack import Attack
from pycats.systems.combat import process_hits


def _player(rect, *, hurtbox_circles, facing_right=True):
    p = types.SimpleNamespace(
        rect=rect, facing_right=facing_right, intangible=False, is_alive=True,
        fighter_data=FighterData(hurtbox=Hurtbox(circles=tuple(hurtbox_circles)), moves={}),
        hits_received=0, hits_landed=0, last_damage=None, last_angle=None,
    )

    def receive_hit(atk, is_crouching=False):
        p.hits_received += 1
        p.last_damage = atk.damage
        p.last_angle = atk.angle

    p.receive_hit = receive_hit
    p.record_hit_landed = lambda: None
    p.fighter = p
    return p


def test_ftilt_is_two_box_tipper_with_tip_first():
    ftilt = load_fighter_data("narz").moves["ftilt"]
    assert ftilt == _NARZ_FTILT  # JSON-backed (#858): equal, not identical (fresh hydrate per load)
    assert len(ftilt.hitboxes) == 2
    tip, base = ftilt.hitboxes
    # the tip is authored FIRST and is the stronger hit
    assert tip.damage > base.damage
    assert tip.base_knockback > base.base_knockback
    assert tip.knockback_growth > base.knockback_growth


def test_tip_beats_base_when_both_overlap():
    """A defender overlapping BOTH boxes takes the TIP's damage (priority = tuple order)."""
    pygame.init()
    # attacker at origin → Hitbox Circle(dx,dy) resolves to absolute (dx,dy).
    attacker = _player(pygame.Rect(0, 0, 40, 60),
                       hurtbox_circles=[Circle(20, 15, 14), Circle(20, 45, 14)])
    # defender hurtbox circle at absolute (60,30): overlaps tip(72,30,r12) AND base(48,30,r14).
    defender = _player(pygame.Rect(40, 0, 40, 60), hurtbox_circles=[Circle(20, 30, 14)])
    atk = Attack(attacker, hitboxes=_NARZ_FTILT.hitboxes, lifetime=4)

    process_hits([attacker, defender], [atk])

    assert defender.hits_received == 1, "two overlapping boxes of one move = one hit"
    assert defender.last_damage == _NARZ_FTILT.hitboxes[0].damage == 13.0, \
        "the TIP (box 0) must win on dual overlap, not the base"


def test_tip_reaches_beyond_the_hurtbox_disjoint():
    narz = load_fighter_data("narz")
    tip = _NARZ_FTILT.hitboxes[0].circle
    hurtbox_outer = max(c.dx + c.r for c in narz.hurtbox.circles)
    # the tip's NEAR edge is past the hurtbox's far edge → a true disjoint
    assert tip.dx - tip.r > hurtbox_outer
