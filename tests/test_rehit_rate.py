"""Rehit-rate / looping multi-hit (#213, a #142 gate, d-air prerequisite).

Today every Attack hits a given target at most once per instance (#130:
`combat.process_hits` sets `atk.active=False` after a hit). A looping move (the
Mario d-air drill) needs a hitbox to re-hit the same target on a cadence.

A `MoveData` may carry `rehit_rate` (frames between re-hits); the spawned Attack
then re-hits an overlapping target every `rehit_rate` frames across its active
window. Moves without it are byte-identical to today (single hit).
"""
from __future__ import annotations

import types

import pygame

from pycats.combat.data import Circle, FighterData, Hitbox, Hurtbox, MoveData
from pycats.entities.attack import Attack
from pycats.systems.combat import process_hits


def _player(rect, *, hurtbox_circles, facing_right=True):
    p = types.SimpleNamespace(
        rect=rect, facing_right=facing_right, invulnerable=False, is_alive=True,
        fighter_data=FighterData(hurtbox=Hurtbox(circles=tuple(hurtbox_circles)),
                                 moves={}),
        hits_received=0, percent=0.0,
    )

    def receive_hit(atk, is_crouching=False):  # #283: combat now passes the crouch flag
        p.hits_received += 1
        p.percent += atk.damage

    p.receive_hit = receive_hit
    p.record_hit_landed = lambda: None
    p.fighter = p
    return p


_DEF_HURTBOX = [Circle(dx=20, dy=30, r=14)]  # defender centre (120,130)


def _overlapping_box(damage=3.0):
    return Hitbox(circle=Circle(dx=120, dy=130, r=14), damage=damage, angle=85,
                  base_knockback=30.0, knockback_growth=80.0)


def _drive(atk, frames):
    """Run process_hits + Attack.update for `frames` frames against a stationary
    overlapping defender; return that defender."""
    owner = _player(pygame.Rect(0, 0, 40, 60), hurtbox_circles=_DEF_HURTBOX)
    defender = _player(pygame.Rect(100, 100, 40, 60), hurtbox_circles=_DEF_HURTBOX)
    for _ in range(frames):
        if atk.frames_left <= 0:
            break
        process_hits([owner, defender], [atk])
        atk.update()
    return defender


# ------------------------------------------------------------------ schema

def test_movedata_rehit_rate_defaults_to_none():
    m = MoveData(name="x", in_air=False, startup=1, active=2, recovery=1,
                 hitboxes=(_overlapping_box(),))
    assert m.rehit_rate is None


def test_movedata_accepts_rehit_rate():
    m = MoveData(name="drill", in_air=True, startup=1, active=20, recovery=1,
                 hitboxes=(_overlapping_box(),), rehit_rate=4)
    assert m.rehit_rate == 4


# ------------------------------------------------------------------ behaviour

def test_looping_attack_rehits_on_cadence():
    """A looping Attack (rehit_rate=4, lifetime 20) hits a stationary overlapping
    defender repeatedly — multiple times across its lifetime."""
    pygame.init()
    owner = _player(pygame.Rect(0, 0, 40, 60), hurtbox_circles=_DEF_HURTBOX)
    atk = Attack(owner, hitboxes=(_overlapping_box(damage=3.0),),
                 lifetime=20, rehit_rate=4)
    defender = _drive(atk, frames=20)
    assert defender.hits_received >= 4, "looping move should connect many times"
    assert defender.percent == defender.hits_received * 3.0


def test_non_looping_attack_hits_once():
    """A normal Attack (no rehit_rate) hits the same target exactly once — the
    #130 once-per-instance guarantee is preserved."""
    pygame.init()
    owner = _player(pygame.Rect(0, 0, 40, 60), hurtbox_circles=_DEF_HURTBOX)
    atk = Attack(owner, hitboxes=(_overlapping_box(damage=3.0),), lifetime=20)
    defender = _drive(atk, frames=20)
    assert defender.hits_received == 1
