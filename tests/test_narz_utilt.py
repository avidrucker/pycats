"""Narz up-tilt — anti-air disjoint tipper arc (slice 5 of #294, #305).

Marth's anti-air: a 2-box tipper (tip first) that hits ABOVE the head (low/negative dy)
and sends upward. The disjoint here is vertical (reaches above the hurtbox), unlike the
f-tilt/d-tilt horizontal reach. Golden-free: sim loads the default cat.
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


def test_utilt_is_two_box_tipper_tip_first():
    utilt = load_fighter_data("narz").moves["utilt"]
    assert utilt.name == "utilt"
    assert len(utilt.hitboxes) == 2
    tip, base = utilt.hitboxes
    assert tip.damage > base.damage
    assert tip.base_knockback > base.base_knockback
    assert tip.knockback_growth > base.knockback_growth


def test_utilt_hits_high_and_sends_up():
    narz = load_fighter_data("narz")
    tip, base = narz.moves["utilt"].hitboxes
    hurtbox_top = min(c.dy - c.r for c in narz.hurtbox.circles)
    # vertical disjoint: the tip's top edge is above the hurtbox top edge
    assert tip.circle.dy - tip.circle.r < hurtbox_top
    assert tip.circle.dy < base.circle.dy          # tip is the higher box
    assert tip.angle > 45                          # upward launch (≈90)


def test_utilt_tip_beats_base_when_both_overlap():
    pygame.init()
    attacker = _player(pygame.Rect(0, 0, 40, 60),
                       hurtbox_circles=[Circle(20, 15, 14), Circle(20, 45, 14)])
    # defender hurtbox circle at absolute (24,0): overlaps tip(24,-8) and base(24,8).
    defender = _player(pygame.Rect(4, -30, 40, 60), hurtbox_circles=[Circle(20, 30, 14)])
    utilt = load_fighter_data("narz").moves["utilt"]
    atk = Attack(attacker, hitboxes=utilt.hitboxes, lifetime=4)

    process_hits([attacker, defender], [atk])

    assert defender.hits_received == 1
    assert defender.last_damage == utilt.hitboxes[0].damage, "the TIP (box 0) must win"
