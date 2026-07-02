"""Narz neutral-air — first sword aerial, disjoint tipper (slice 6 of #294, #307).

The first Narz `in_air=True` move (the air/ground split, #38): a 2-box tipper sword
swipe around the body, disjoint. Golden-free: sim loads the default cat.
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


def test_nair_is_an_aerial_two_box_tipper():
    nair = load_fighter_data("narz").moves["nair"]
    assert nair.name == "nair"
    assert nair.in_air is True                     # the first Narz aerial (air/ground split)
    assert len(nair.hitboxes) == 2
    tip, base = nair.hitboxes
    assert tip.damage > base.damage
    assert tip.base_knockback > base.base_knockback
    assert tip.knockback_growth > base.knockback_growth


def test_nair_is_disjoint():
    narz = load_fighter_data("narz")
    tip = narz.moves["nair"].hitboxes[0].circle
    hurtbox_outer = max(c.dx + c.r for c in narz.hurtbox.circles)
    assert tip.dx - tip.r > hurtbox_outer


def test_nair_tip_beats_base_when_both_overlap():
    pygame.init()
    attacker = _player(pygame.Rect(0, 0, 40, 60),
                       hurtbox_circles=[Circle(20, 15, 14), Circle(20, 45, 14)])
    # defender hurtbox circle at absolute (50,30): overlaps tip(60,30) and base(40,30).
    defender = _player(pygame.Rect(30, 0, 40, 60), hurtbox_circles=[Circle(20, 30, 14)])
    nair = load_fighter_data("narz").moves["nair"]
    atk = Attack(attacker, hitboxes=nair.hitboxes, in_air=True, lifetime=4)

    process_hits([attacker, defender], [atk])

    assert defender.hits_received == 1
    assert defender.last_damage == nair.hitboxes[0].damage, "the TIP (box 0) must win"
