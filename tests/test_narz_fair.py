"""Narz forward-air — the iconic disjoint tipper spacing aerial (slice 7 of #294, #313).

Marth's signature wall: a 2-box tipper (tip first) forward sword swipe with the longest
disjoint reach of the kit. Golden-free: sim loads the default cat.
"""
from __future__ import annotations
import types
import pygame

from pycats.combat.data import Circle, Hurtbox, FighterData, load_fighter_data
from pycats.entities.attack import Attack
from pycats.systems.combat import process_hits


def _player(rect, *, hurtbox_circles, facing_right=True):
    p = types.SimpleNamespace(
        rect=rect, facing_right=facing_right, invulnerable=False, is_alive=True,
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


def test_fair_is_an_aerial_two_box_tipper():
    fair = load_fighter_data("narz").moves["fair"]
    assert fair.name == "fair"
    assert fair.in_air is True
    assert len(fair.hitboxes) == 2
    tip, base = fair.hitboxes
    assert tip.damage > base.damage
    assert tip.base_knockback > base.base_knockback
    assert tip.knockback_growth > base.knockback_growth


def test_fair_is_the_longest_reaching_disjoint():
    narz = load_fighter_data("narz")
    tip = narz.moves["fair"].hitboxes[0].circle
    hurtbox_outer = max(c.dx + c.r for c in narz.hurtbox.circles)
    assert tip.dx - tip.r > hurtbox_outer                       # disjoint
    # the dedicated spacer reaches farther than the n-air tip
    assert tip.dx > narz.moves["nair"].hitboxes[0].circle.dx


def test_fair_tip_beats_base_when_both_overlap():
    pygame.init()
    attacker = _player(pygame.Rect(0, 0, 40, 60),
                       hurtbox_circles=[Circle(20, 15, 14), Circle(20, 45, 14)])
    # defender hurtbox circle at absolute (58,29): overlaps tip(70,28) and base(46,30).
    defender = _player(pygame.Rect(38, -1, 40, 60), hurtbox_circles=[Circle(20, 30, 14)])
    fair = load_fighter_data("narz").moves["fair"]
    atk = Attack(attacker, hitboxes=fair.hitboxes, in_air=True, lifetime=4)

    process_hits([attacker, defender], [atk])

    assert defender.hits_received == 1
    assert defender.last_damage == fair.hitboxes[0].damage, "the TIP (box 0) must win"
