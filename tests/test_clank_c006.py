"""tests/test_clank_c006.py — fresh red-green pin for PYC-C-006-GRAPE (#1000).

PYC-C-006-GRAPE — opposing-hitbox clank / priority (#38):
    Two overlapping active **GROUND** hitboxes owned by *different* fighters are
    resolved by a damage "priority range" of `CLANK_PRIORITY_RANGE` (9%, from
    SmashWiki's Melee/Brawl/PM family value):
      - |dmg_a - dmg_b| <= 9  ->  BOTH hitboxes end this frame (mutual clank);
      - otherwise            ->  the STRONGER survives, the weaker ends.
    Aerials never clank (gated on `Attack.in_air`). The clank resolves BEFORE
    the attack->defender pass, so a mutually-clanked pair damages no bystander
    caught in the overlap. pycats has no rebound/hitlag yet (#38 later slices):
    a clank only NEGATES the losing hitbox(es) for the frame (PYC-C-007-GRAPE).

Mechanism under test: `pycats/systems/hit_resolution.py` — `_resolve_clanks`
(the pairing + 9%-window decision) and its call site in `process_hits`
(ordered before attack->defender). NOTE: the C-006 ledger header cited the
pre-rename `systems/combat.py`; the module is `systems/hit_resolution.py` as of
commit 481edcf.

These tests are authored fresh (not the pre-existing tests/test_clank.py, which
#872 pinned via an ephemeral mutation). Each is proven able-to-fail by a NAMED
source mutation:

  M1 — neuter the within-range branch:
       `if abs(da - db) <= CLANK_PRIORITY_RANGE:` -> `if False:`
       => within-range pairs fall through to the stronger-survives arm.
       Reds T1 (and, collaterally, the bystander T4 — both depend on
       within-range -> both-end; T4's own designated proof is M4).
  M2 — invert the priority comparison: `elif da > db:` -> `elif da < db:`
       => over-range pairs keep the WEAKER. Reds T2 only.
  M3 — drop the aerial gate:
       `[a for a in attacks if a.active and not getattr(a, "in_air", False)]`
       -> `[a for a in attacks if a.active]`
       => aerials clank. Reds T3 only.
  M4 — move `_resolve_clanks(attacks)` in `process_hits` to AFTER the
       attack->defender loop => a bystander is hit before the clank negates.
       Reds T4 only.

Boundary coverage: T1 asserts diff == 9 (the `<=` inclusive edge) both-ends and
T2 asserts diff == 10 stronger-survives, so the pair also pins the exact `<= 9`
threshold against a `<=` -> `<` off-by-one.

Geometry: attacker A rect (0,0) facing right + box dx=120 resolves to abs centre
(120,130); attacker B rect (200,100) facing left + box dx=120 resolves to the
same (120,130) — so A and B always overlap.
"""

from __future__ import annotations

import types

import pygame

from pycats.combat.data import Circle, FighterData, Hitbox, Hurtbox
from pycats.config import CLANK_PRIORITY_RANGE
from pycats.entities.attack import Attack
from pycats.systems.hit_resolution import process_hits


def _fighter(rect, *, facing_right, hurtbox_circle):
    """A minimal duck-typed Player/fighter stand-in for hit resolution."""
    p = types.SimpleNamespace(
        rect=rect,
        facing_right=facing_right,
        intangible=False,
        is_alive=True,
        fighter_data=FighterData(walk=1.1, dash=1.5, run=1.5, hurtbox=Hurtbox(circles=(hurtbox_circle,)), moves={}),
        hits_received=0,
        hits_landed=0,
    )
    p.receive_hit = lambda atk, **kw: setattr(p, "hits_received", p.hits_received + 1)
    p.record_hit_landed = lambda: setattr(p, "hits_landed", p.hits_landed + 1)
    p.fighter = p  # Attack/hit_resolution read owner.fighter.facing_right etc.
    return p


def _attacker(rect, *, facing_right):
    # hurtbox far from the (120,130) clank point so attackers never hit each other,
    # isolating the clank outcome from the attack->defender pass.
    return _fighter(rect, facing_right=facing_right, hurtbox_circle=Circle(dx=20, dy=30, r=14))


def _atk(owner, damage, *, in_air=False):
    """A single-box attack whose circle resolves to abs (120,130) for both
    owners (dx=120: A facing right -> 0+120; B facing left -> 200+40-120)."""
    hb = Hitbox(
        circle=Circle(dx=120, dy=130 if owner.facing_right else 30, r=20),
        damage=damage,
        angle=0,
        base_knockback=30.0,
        knockback_growth=80.0,
    )
    return Attack(owner, hitbox=hb, lifetime=4, in_air=in_air)


def _clash(dmg_a, dmg_b, *, a_in_air=False, b_in_air=False):
    a_owner = _attacker(pygame.Rect(0, 0, 40, 60), facing_right=True)
    b_owner = _attacker(pygame.Rect(200, 100, 40, 60), facing_right=False)
    a = _atk(a_owner, dmg_a, in_air=a_in_air)
    b = _atk(b_owner, dmg_b, in_air=b_in_air)
    return a_owner, b_owner, a, b


def test_c006_within_9pct_both_hitboxes_end():
    """|dmg_a - dmg_b| <= 9 -> both end. Covers equal (diff 0) and the inclusive
    boundary (diff exactly 9). Able-to-fail: M1."""
    pygame.init()
    for dmg_a, dmg_b, why in ((10.0, 10.0, "equal damage"), (19.0, 10.0, "diff == 9 (inclusive edge)")):
        a_owner, b_owner, a, b = _clash(dmg_a, dmg_b)
        process_hits([a_owner, b_owner], [a, b])
        assert a.active is False and b.active is False, f"within 9% -> both clank ({why})"


def test_c006_over_9pct_stronger_survives_weaker_ends():
    """|dmg_a - dmg_b| > 9 -> stronger survives, weaker ends. Covers the boundary
    (diff exactly 10) and a clearly-over case. Able-to-fail: M2."""
    pygame.init()
    for dmg_a, dmg_b, why in ((20.0, 10.0, "diff == 10 (just over the edge)"), (25.0, 10.0, "diff 15")):
        a_owner, b_owner, a, b = _clash(dmg_a, dmg_b)
        process_hits([a_owner, b_owner], [a, b])
        assert a.active is True, f"stronger hitbox survives the clank ({why})"
        assert b.active is False, f"weaker hitbox ends ({why})"


def test_c006_aerial_never_clanks():
    """An aerial hitbox is excluded from the clank pass entirely — even a matched
    ground opponent it overlaps stays live. Able-to-fail: M3."""
    pygame.init()
    a_owner, b_owner, a, b = _clash(10.0, 10.0, a_in_air=True)
    process_hits([a_owner, b_owner], [a, b])
    assert a.active is True and b.active is True, "an aerial does not clank a ground hitbox"


def test_c006_mutual_clank_damages_no_caught_bystander():
    """The clank resolves before attack->defender, so a defender sitting in the
    overlap of a mutually-clanked (within-9%) pair takes no hit. Able-to-fail: M4."""
    pygame.init()
    a_owner, b_owner, a, b = _clash(10.0, 10.0)
    # defender hurtbox centre (126,130): overlaps both boxes at (120,130).
    defender = _fighter(pygame.Rect(106, 100, 40, 60), facing_right=True, hurtbox_circle=Circle(dx=20, dy=30, r=14))
    process_hits([a_owner, b_owner, defender], [a, b])
    assert defender.hits_received == 0, "both hitboxes clank away before they can hit a bystander"
    assert a.active is False and b.active is False, "the pair still mutually clanks"


def test_c006_priority_range_is_9():
    """Guard the sourced constant itself (SmashWiki 9% family value) so an
    unannounced retune of the window is caught alongside the behavioural pins."""
    assert CLANK_PRIORITY_RANGE == 9
