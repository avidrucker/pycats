"""Narz down-tilt — low disjoint tipper poke (slice 4 of #294, #303).

Marth's low spacing / edgeguard tool: a 2-box tipper (tip first) like the f-tilt, but
near the feet (high dy) and at a low launch angle. Reuses the f-tilt's tipper proof
(tip wins on dual overlap). Golden-free: sim loads the default cat.
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


def test_dtilt_is_two_box_tipper_tip_first():
    dtilt = load_fighter_data("narz").moves["dtilt"]
    assert dtilt.name == "dtilt"
    assert len(dtilt.hitboxes) == 2
    tip, base = dtilt.hitboxes
    assert tip.damage > base.damage
    assert tip.base_knockback > base.base_knockback
    assert tip.knockback_growth > base.knockback_growth


def test_dtilt_is_low_and_disjoint():
    narz = load_fighter_data("narz")
    tip = narz.moves["dtilt"].hitboxes[0].circle
    hurtbox_outer = max(c.dx + c.r for c in narz.hurtbox.circles)
    assert tip.dx - tip.r > hurtbox_outer          # disjoint reach
    assert tip.dy > 30                             # low — near the feet (body is 60 tall)


def test_dtilt_tip_beats_base_when_both_overlap():
    pygame.init()
    attacker = _player(pygame.Rect(0, 0, 40, 60),
                       hurtbox_circles=[Circle(20, 15, 14), Circle(20, 45, 14)])
    # defender hurtbox circle at absolute (55,47): overlaps tip(66,46) and base(44,48).
    defender = _player(pygame.Rect(35, 17, 40, 60), hurtbox_circles=[Circle(20, 30, 14)])
    dtilt = load_fighter_data("narz").moves["dtilt"]
    atk = Attack(attacker, hitboxes=dtilt.hitboxes, lifetime=4)

    process_hits([attacker, defender], [atk])

    assert defender.hits_received == 1
    assert defender.last_damage == dtilt.hitboxes[0].damage, "the TIP (box 0) must win"


def test_dtilt_sends_low():
    # a low-trajectory poke (edgeguard tool) — not the f-tilt's 361 sentinel
    dtilt = load_fighter_data("narz").moves["dtilt"]
    assert dtilt.hitboxes[0].angle < 90
