"""Narz up-air — overhead juggle arc, disjoint tipper (slice 9 of #294, #323).

Marth's juggle aerial: a 2-box tipper (tip first) hitting ABOVE the fighter (low/negative
dy) and sending up — the up-tilt's vertical disjoint, as an aerial. Golden-free: sim loads
the default cat.
"""
from __future__ import annotations

import types

import pygame

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


def test_uair_is_an_aerial_two_box_tipper():
    uair = load_fighter_data("narz").moves["uair"]
    assert uair.name == "uair"
    assert uair.in_air is True
    assert len(uair.hitboxes) == 2
    tip, base = uair.hitboxes
    assert tip.damage > base.damage
    assert tip.base_knockback > base.base_knockback
    assert tip.knockback_growth > base.knockback_growth


def test_uair_hits_high_and_sends_up():
    narz = load_fighter_data("narz")
    tip, base = narz.moves["uair"].hitboxes
    hurtbox_top = min(c.dy - c.r for c in narz.hurtbox.circles)
    assert tip.circle.dy - tip.circle.r < hurtbox_top    # vertical disjoint (above)
    assert tip.circle.dy < base.circle.dy                # tip is the higher box
    assert tip.angle > 45                                # upward launch (≈90)


def test_uair_tip_beats_base_when_both_overlap():
    pygame.init()
    attacker = _player(pygame.Rect(0, 0, 40, 60),
                       hurtbox_circles=[Circle(20, 15, 14), Circle(20, 45, 14)])
    # defender hurtbox circle at absolute (22,0): overlaps tip(22,-10) and base(22,8).
    defender = _player(pygame.Rect(2, -30, 40, 60), hurtbox_circles=[Circle(20, 30, 14)])
    uair = load_fighter_data("narz").moves["uair"]
    atk = Attack(attacker, hitboxes=uair.hitboxes, in_air=True, lifetime=4)

    process_hits([attacker, defender], [atk])

    assert defender.hits_received == 1
    assert defender.last_damage == uair.hitboxes[0].damage, "the TIP (box 0) must win"
