"""tests/test_multihit_c003.py

Fresh red-green pinning of **PYC-C-003-GRAPE** (#997, successor to the closed #872
verification pass, which showed non-vacuity only by an ephemeral mutation).

Claim ID: PYC-C-003-GRAPE
Statement: A plain pycats multi-hitbox move (#130) — several hitbox circles in one
active window, no `rehit_rate` — hits a target EXACTLY ONCE. When the move overlaps
a target, only the FIRST box in priority (tuple) order registers, and its params are
applied; the extra overlapping boxes never add a second hit. Enforced in
`systems/combat.py:process_hits` (`next(...)` picks the first overlapping box, then
`break` after the connect). Multi-hitbox is NOT multi-hit.

The claim has two conjuncts; each test below is proven able-to-fail by a named
source mutation (revert-check), then reverted to green:

  M1 — once-per-target. Replace the single `next(...)` connect with a loop that
       applies EVERY overlapping box (the "multi-hitbox = multi-hit" regression the
       #130 feature exists to prevent). Reds test_c003_two_overlapping_boxes_hit_once
       (hits_received 1 -> 2). THE claim-negating mutation for the headline conjunct.

  M2 — first-box priority. Iterate the boxes in REVERSED order in the `next(...)`,
       so the LAST overlapping box wins instead of the first. Reds
       test_c003_first_box_in_priority_order_wins (last_damage 9 -> 5, last_angle
       80 -> 361); the hit count is unchanged, so it isolates the priority conjunct.

  M3 — priority walks past missing boxes. Restrict the connect to boxes[0] only
       (the pre-#130 "drop everything past hitboxes[0]" behavior). Reds
       test_c003_priority_walks_past_missing_boxes (a move whose only overlapping box
       is box[2] registers 0 hits); leaves M1/M2's tests green.

Geometry (matches the #130 harness): attacker rect at (0,0) facing right, so a
Hitbox Circle(dx,dy,r) resolves to absolute centre (dx,dy). Defender rect at
(100,100,40,60) with a single hurtbox circle dx=20,dy=30,r=14 -> absolute (120,130).
Boxes near (120,130) overlap; boxes out at x=300+ miss.
"""

from __future__ import annotations

import types

import pygame

from pycats.combat.data import Circle, FighterData, Hitbox, Hurtbox
from pycats.entities.attack import Attack
from pycats.systems.combat import process_hits


def _player(rect, *, hurtbox_circles, facing_right=True, intangible=False, is_alive=True):
    """A lightweight defender/attacker stub: real hurtbox + real receive_hit
    counter, no full game loop. Mirrors the #130 multi-hitbox harness."""
    p = types.SimpleNamespace(
        rect=rect,
        facing_right=facing_right,
        intangible=intangible,
        is_alive=is_alive,
        fighter_data=FighterData(hurtbox=Hurtbox(circles=tuple(hurtbox_circles)), moves={}),
        hits_received=0,
        hits_landed=0,
        last_damage=None,
        last_angle=None,
    )

    def receive_hit(atk, is_crouching=False):
        p.hits_received += 1
        p.last_damage = atk.damage
        p.last_angle = atk.angle

    def record_hit_landed():
        p.hits_landed += 1

    p.receive_hit = receive_hit
    p.record_hit_landed = record_hit_landed
    p.fighter = p
    return p


_DEF_HURTBOX = [Circle(dx=20, dy=30, r=14)]  # defender centre (120,130)


def _hb(dx, dy, r, *, damage, angle):
    return Hitbox(
        circle=Circle(dx=dx, dy=dy, r=r), damage=damage, angle=angle, base_knockback=30.0, knockback_growth=80.0
    )


def test_c003_two_overlapping_boxes_hit_once():
    """Conjunct (once-per-target): a defender overlapping TWO boxes of one plain
    move takes exactly one hit. Able-to-fail via M1 (apply every overlapping box
    -> hits_received == 2). Claim: PYC-C-003-GRAPE."""
    pygame.init()
    owner = _player(pygame.Rect(0, 0, 40, 60), hurtbox_circles=_DEF_HURTBOX)
    defender = _player(pygame.Rect(100, 100, 40, 60), hurtbox_circles=_DEF_HURTBOX)

    move_boxes = (
        _hb(120, 130, 12, damage=9, angle=80),  # box[0] — overlaps
        _hb(118, 130, 12, damage=5, angle=361),  # box[1] — also overlaps
    )
    atk = Attack(owner, hitboxes=move_boxes, lifetime=4)

    process_hits([owner, defender], [atk])

    assert defender.hits_received == 1, (
        "two overlapping boxes of one move must be a single hit (multi-hitbox != multi-hit)"
    )


def test_c003_first_box_in_priority_order_wins():
    """Conjunct (first-box priority): when two boxes overlap, the params applied are
    the FIRST box's (priority order), not a later box's. Able-to-fail via M2 (reverse
    the box order -> the last box's params win). Claim: PYC-C-003-GRAPE."""
    pygame.init()
    owner = _player(pygame.Rect(0, 0, 40, 60), hurtbox_circles=_DEF_HURTBOX)
    defender = _player(pygame.Rect(100, 100, 40, 60), hurtbox_circles=_DEF_HURTBOX)

    move_boxes = (
        _hb(120, 130, 12, damage=9, angle=80),  # box[0] — priority, overlaps
        _hb(118, 130, 12, damage=5, angle=361),  # box[1] — also overlaps
    )
    atk = Attack(owner, hitboxes=move_boxes, lifetime=4)

    process_hits([owner, defender], [atk])

    assert defender.last_damage == 9, "the first (priority) box's damage must be the one applied"
    assert defender.last_angle == 80, "the first (priority) box's angle must be the one applied"


def test_c003_priority_walks_past_missing_boxes():
    """Conjunct (first-box priority, walk-past facet): priority resolution walks past
    non-overlapping earlier boxes and lands the first box that actually overlaps, with
    ITS params — a move whose only overlapping box is box[2] still connects exactly once
    (the #130 fix over the pre-#130 'boxes[0] only' engine). Able-to-fail via M3 (consider
    boxes[0] only -> 0 hits). Claim: PYC-C-003-GRAPE."""
    pygame.init()
    owner = _player(pygame.Rect(0, 0, 40, 60), hurtbox_circles=_DEF_HURTBOX)
    defender = _player(pygame.Rect(100, 100, 40, 60), hurtbox_circles=_DEF_HURTBOX)

    move_boxes = (
        _hb(300, 130, 10, damage=99, angle=0),  # box[0] — far, misses
        _hb(320, 130, 10, damage=99, angle=0),  # box[1] — far, misses
        _hb(120, 130, 12, damage=8, angle=80),  # box[2] — overlaps (120,130)
    )
    atk = Attack(owner, hitboxes=move_boxes, lifetime=4)

    process_hits([owner, defender], [atk])

    assert defender.hits_received == 1, "the first overlapping box (box[2]) must connect exactly once"
    assert defender.last_damage == 8, "the connecting box's (box[2]) damage must be applied"
    assert defender.last_angle == 80, "the connecting box's (box[2]) angle must be applied"
