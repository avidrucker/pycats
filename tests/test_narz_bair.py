"""Narz back-air — disjoint tipper backward swipe (slice 8 of #294, #316).

Marth's backward KO/spacing poke: a 2-box tipper (tip first) BEHIND the body (negative
dx), disjoint. Golden-free: sim loads the default cat.
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


def test_bair_is_an_aerial_two_box_tipper():
    bair = load_fighter_data("narz").moves["bair"]
    assert bair.name == "bair"
    assert bair.in_air is True
    assert len(bair.hitboxes) == 2
    tip, base = bair.hitboxes
    assert tip.damage > base.damage
    assert tip.base_knockback > base.base_knockback
    assert tip.knockback_growth > base.knockback_growth


def test_bair_is_disjoint_behind_the_body():
    narz = load_fighter_data("narz")
    tip = narz.moves["bair"].hitboxes[0].circle
    hurtbox_back = min(c.dx - c.r for c in narz.hurtbox.circles)
    # the box is wholly BEHIND the body: its front edge is behind the hurtbox back edge
    assert tip.dx + tip.r < hurtbox_back


def test_bair_tip_beats_base_when_both_overlap():
    pygame.init()
    attacker = _player(pygame.Rect(0, 0, 40, 60),
                       hurtbox_circles=[Circle(20, 15, 14), Circle(20, 45, 14)])
    # defender hurtbox circle at absolute (-53,29): overlaps tip(-64,28) and base(-42,30).
    defender = _player(pygame.Rect(-73, -1, 40, 60), hurtbox_circles=[Circle(20, 30, 14)])
    bair = load_fighter_data("narz").moves["bair"]
    atk = Attack(attacker, hitboxes=bair.hitboxes, in_air=True, lifetime=4)

    process_hits([attacker, defender], [atk])

    assert defender.hits_received == 1
    assert defender.last_damage == bair.hitboxes[0].damage, "the TIP (box 0) must win"
