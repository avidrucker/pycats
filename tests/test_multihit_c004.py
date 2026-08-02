"""tests/test_multihit_c004.py

Fresh red-green pinning of **PYC-C-004-GRAPE** (#998, successor to the closed #872
verification pass, which showed non-vacuity only by an ephemeral mutation).

Claim ID: PYC-C-004-GRAPE
Statement: pycats supports REAL multi-hit against a single target via looping
`rehit_rate=N` (#213). On each connect `systems/hit_resolution.py:process_hits` puts the
attack on an N-frame cooldown (`_rehit_timer`) instead of ending it; `Attack.update`
drains that cooldown, so the SAME stationary overlapping target is struck repeatedly
across the move's active window — not once. A move without `rehit_rate` keeps the #130
once-per-instance guarantee (exactly one hit), so the extra hits are attributable to the
looping mechanism.

The claim has two conjuncts; each test below is proven able-to-fail by a named source
mutation (revert-check), then reverted to green:

  M1 — disable the rehit re-arm. In `process_hits`, make the connect deactivate a
       `rehit_rate` attack instead of arming its cooldown (replace the
       `atk._rehit_timer = atk.rehit_rate` branch with `atk.active = False`, the
       once-per-instance path). This collapses a looping move onto a single-hit move.
       Reds test_c004_looping_rehit_hits_one_target_many_times (hits_received 5 -> 1).
       THE claim-negating mutation for the headline conjunct.

  M2 — drop the single-hit deactivation. In `process_hits`, make a NO-`rehit_rate`
       connect keep the attack active (replace the else `atk.active = False` with
       `pass`), so a plain attack re-hits every frame it overlaps. Reds
       test_c004_non_looping_attack_hits_target_once (hits_received 1 -> 20); leaves
       M1's looping test green. Proves the contrast test non-vacuous — a plain move's
       once-ness is a real, breakable property, so the looping move's extra hits are
       attributable to `rehit_rate`, not to the harness always counting one.

Geometry (matches the #130 / test_rehit_rate harness): attacker rect at (0,0) facing
right, so a Hitbox Circle(dx,dy,r) resolves to absolute centre (dx,dy). Defender rect at
(100,100,40,60) with a single hurtbox circle dx=20,dy=30,r=14 -> absolute (120,130). The
move's box sits on (120,130) and overlaps for the whole lifetime (a STATIONARY target).
"""

from __future__ import annotations

import types

import pygame

from pycats.combat.data import Circle, FighterData, Hitbox, Hurtbox
from pycats.entities.attack import Attack
from pycats.systems.hit_resolution import process_hits


def _player(rect, *, hurtbox_circles, facing_right=True, intangible=False, is_alive=True):
    """A lightweight defender/attacker stub: real hurtbox + real receive_hit
    counter, no full game loop. Mirrors the #130 / #213 rehit harness."""
    p = types.SimpleNamespace(
        rect=rect,
        facing_right=facing_right,
        intangible=intangible,
        is_alive=is_alive,
        fighter_data=FighterData(hurtbox=Hurtbox(circles=tuple(hurtbox_circles)), moves={}),
        hits_received=0,
        hits_landed=0,
        percent=0.0,
    )

    def receive_hit(atk, is_crouching=False):  # #283: combat now passes the crouch flag
        p.hits_received += 1
        p.percent += atk.damage

    def record_hit_landed():
        p.hits_landed += 1

    p.receive_hit = receive_hit
    p.record_hit_landed = record_hit_landed
    p.fighter = p
    return p


_DEF_HURTBOX = [Circle(dx=20, dy=30, r=14)]  # defender centre (120,130)


def _overlapping_box(damage=3.0):
    return Hitbox(
        circle=Circle(dx=120, dy=130, r=14), damage=damage, angle=85, base_knockback=30.0, knockback_growth=80.0
    )


def _drive(atk, frames):
    """Run process_hits + Attack.update for `frames` frames against a STATIONARY
    overlapping defender; return that defender. This is the loop over the move's
    lifetime — process_hits registers a hit only when the rehit cooldown has
    drained, and Attack.update drains it, so the hits play out across frames."""
    owner = _player(pygame.Rect(0, 0, 40, 60), hurtbox_circles=_DEF_HURTBOX)
    defender = _player(pygame.Rect(100, 100, 40, 60), hurtbox_circles=_DEF_HURTBOX)
    for _ in range(frames):
        if atk.frames_left <= 0:
            break
        process_hits([owner, defender], [atk])
        atk.update()
    return defender


def test_c004_looping_rehit_hits_one_target_many_times():
    """Conjunct (looping multi-hit over the lifetime): a `rehit_rate=4` attack over a
    20-frame lifetime strikes a stationary overlapping target MANY times (not once),
    and the accumulated percent is the per-hit damage times the hit count. Able-to-fail
    via M1 (disable the rehit re-arm -> the attack deactivates after one connect ->
    hits_received == 1). Claim: PYC-C-004-GRAPE."""
    pygame.init()
    owner = _player(pygame.Rect(0, 0, 40, 60), hurtbox_circles=_DEF_HURTBOX)
    atk = Attack(owner, hitboxes=(_overlapping_box(damage=3.0),), lifetime=20, rehit_rate=4)

    defender = _drive(atk, frames=20)

    assert defender.hits_received >= 4, (
        "a rehit_rate attack must re-connect on its cooldown across the lifetime "
        "(real multi-hit against one target), not hit once"
    )
    assert defender.percent == defender.hits_received * 3.0, "every looping connect applies the box's damage"


def test_c004_non_looping_attack_hits_target_once():
    """Conjunct (no-`rehit_rate` = once, the contrast): the SAME attack without
    `rehit_rate` hits the same stationary overlapping target EXACTLY ONCE over the
    identical 20-frame drive — so the extra hits in the looping case are attributable
    to the `rehit_rate` mechanism, not the harness. Able-to-fail via M2 (drop the
    single-hit deactivation -> a plain attack re-hits every overlapping frame ->
    hits_received == 20). Claim: PYC-C-004-GRAPE."""
    pygame.init()
    owner = _player(pygame.Rect(0, 0, 40, 60), hurtbox_circles=_DEF_HURTBOX)
    atk = Attack(owner, hitboxes=(_overlapping_box(damage=3.0),), lifetime=20)  # no rehit_rate

    defender = _drive(atk, frames=20)

    assert defender.hits_received == 1, (
        "a move without rehit_rate keeps the #130 once-per-instance guarantee "
        "even while overlapping the target for its whole lifetime"
    )
