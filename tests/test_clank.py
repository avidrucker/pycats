"""tests/test_clank.py

Opposing-hitbox clank/priority (#38 slice 4c, #133).

When two opposing fighters' active GROUND hitboxes overlap, they clank by the
Smash priority rule (SmashWiki: 9% "priority range"):
  - damage difference within 9%  -> BOTH attacks end (neither connects),
  - difference greater than 9%   -> the stronger continues, the weaker ends.

pycats has no rebound state / hitlag yet (later #38 slices), so a clank here
NEGATES the losing hitbox(es) for the frame — it does not (yet) freeze or
rebound the fighter. Aerials do not clank (SmashWiki); gated on Attack.in_air.

Geometry: attacker A at (0,0) facing right, attacker B at (200,100) facing left,
both with a hitbox resolving to absolute centre (120,130) so they overlap.
"""
from __future__ import annotations

import types

import pygame

from pycats.combat.data import Circle, FighterData, Hitbox, Hurtbox
from pycats.entities.attack import Attack
from pycats.systems.combat import process_hits

_HURT = [Circle(dx=20, dy=30, r=14)]


def _player(rect, *, facing_right=True, hurtbox=_HURT):
    p = types.SimpleNamespace(
        rect=rect, facing_right=facing_right, invulnerable=False, is_alive=True,
        fighter_data=FighterData(hurtbox=Hurtbox(circles=tuple(hurtbox)), moves={}),
        hits_received=0, hits_landed=0,
    )
    p.receive_hit = lambda atk: setattr(p, "hits_received", p.hits_received + 1)
    p.record_hit_landed = lambda: setattr(p, "hits_landed", p.hits_landed + 1)
    p.fighter = p
    return p


def _atk(owner, dx, dy, r, damage, *, in_air=False):
    hb = Hitbox(circle=Circle(dx=dx, dy=dy, r=r), damage=damage, angle=0,
                base_knockback=30.0, knockback_growth=80.0)
    return Attack(owner, hitbox=hb, lifetime=4, in_air=in_air)


def _two_overlapping(dmg_a, dmg_b, *, a_in_air=False, b_in_air=False):
    a_owner = _player(pygame.Rect(0, 0, 40, 60), facing_right=True)
    b_owner = _player(pygame.Rect(200, 100, 40, 60), facing_right=False)
    a = _atk(a_owner, 120, 130, 20, dmg_a, in_air=a_in_air)       # abs (120,130)
    b = _atk(b_owner, 120, 30, 20, dmg_b, in_air=b_in_air)        # abs (120,130)
    return a_owner, b_owner, a, b


def test_equal_damage_ground_attacks_both_clank():
    pygame.init()
    a_owner, b_owner, a, b = _two_overlapping(10, 10)
    process_hits([a_owner, b_owner], [a, b])
    assert a.active is False and b.active is False, "equal-damage hits should both clank"


def test_within_priority_range_both_clank():
    """8% difference (<= 9) -> both end."""
    pygame.init()
    a_owner, b_owner, a, b = _two_overlapping(18, 10)
    process_hits([a_owner, b_owner], [a, b])
    assert a.active is False and b.active is False, "within 9% -> both clank"


def test_stronger_attack_survives_when_diff_over_9():
    """12% difference (> 9) -> stronger (a) survives, weaker (b) ends."""
    pygame.init()
    a_owner, b_owner, a, b = _two_overlapping(20, 8)
    process_hits([a_owner, b_owner], [a, b])
    assert a.active is True, "stronger attack should survive a clank"
    assert b.active is False, "weaker attack should be negated"


def test_clanked_attacks_deal_no_damage_to_a_caught_defender():
    """A defender sitting in the clank overlap takes no hit, because clank
    resolves before attack->player and both equal hits are negated."""
    pygame.init()
    a_owner, b_owner, a, b = _two_overlapping(10, 10)
    defender = _player(pygame.Rect(106, 100, 40, 60))  # hurtbox centre (126,130)
    process_hits([a_owner, b_owner, defender], [a, b])
    assert defender.hits_received == 0, "clanked hitboxes must not damage a bystander"


def test_aerial_does_not_clank_with_ground():
    pygame.init()
    a_owner, b_owner, a, b = _two_overlapping(10, 10, a_in_air=True)
    process_hits([a_owner, b_owner], [a, b])
    assert a.active is True and b.active is True, "an aerial does not clank"
