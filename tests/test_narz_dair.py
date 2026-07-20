"""Narz down-air — meteor spike, disjoint tipper (slice 10 of #294, #324).

Marth's meteor: a 2-box tipper (tip first) below the fighter (high dy) with a downward
spike angle. The stall-then-fall MOVEMENT is out of scope (a movement mechanic, kin to
fast-fall #261) — this pins the spike hitbox only. Golden-free: sim loads the default cat.
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


def test_dair_is_an_aerial_two_box_tipper():
    dair = load_fighter_data("narz").moves["dair"]
    assert dair.name == "dair"
    assert dair.in_air is True
    assert len(dair.hitboxes) == 2
    tip, base = dair.hitboxes
    assert tip.damage > base.damage
    assert tip.base_knockback > base.base_knockback
    assert tip.knockback_growth > base.knockback_growth


def test_dair_spikes_below_the_body():
    narz = load_fighter_data("narz")
    tip = narz.moves["dair"].hitboxes[0]
    hurtbox_bottom = max(c.dy + c.r for c in narz.hurtbox.circles)
    # disjoint below: the tip's top edge is below the hurtbox bottom edge
    assert tip.circle.dy - tip.circle.r > hurtbox_bottom
    assert tip.angle == 270                        # straight-down meteor spike


def test_dair_tip_beats_base_when_both_overlap():
    pygame.init()
    attacker = _player(pygame.Rect(0, 0, 40, 60),
                       hurtbox_circles=[Circle(20, 15, 14), Circle(20, 45, 14)])
    # defender hurtbox circle at absolute (24,66): overlaps tip(24,76) and base(24,56).
    defender = _player(pygame.Rect(4, 36, 40, 60), hurtbox_circles=[Circle(20, 30, 14)])
    dair = load_fighter_data("narz").moves["dair"]
    atk = Attack(attacker, hitboxes=dair.hitboxes, in_air=True, lifetime=4)

    process_hits([attacker, defender], [atk])

    assert defender.hits_received == 1
    assert defender.last_damage == dair.hitboxes[0].damage, "the TIP (box 0) must win"
