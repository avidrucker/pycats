"""Narrow anti-stall backstop — break a detected no-progress lock (#368, epic #365).

Per the #376 verdict this is NOT a blanket idle timer (that would kill legit spacing).
It fires only on a genuine no-progress lock: a leveled bot stuck within ANTI_STALL_MOVE_PX
with no hit landing either way and a reachable target, sustained ANTI_STALL_MAX frames —
then injects one toward-target progress action. Since #369 removed the only natural lock,
these tests SYNTHESIZE a frozen config (call decide() without stepping physics).
"""
import random

import pygame as pg

from pycats.sim.runner import build_players
from pycats.sim.controllers import AttackerController, ANTI_STALL_MAX, ANTI_STALL_MOVE_PX


def _frozen_pair():
    pg.init()
    p1, p2, _ = build_players("nalio", "birky")
    for p in (p1, p2):
        p.fighter.on_ground = True
    p1.rect.x, p1.rect.y = 300, 300
    p2.rect.x, p2.rect.y = 320, 300          # adx≈20, p2 to p1's right, same level
    p1.fighter.facing_right, p2.fighter.facing_right = True, False
    return p1, p2


def test_backstop_injects_toward_target_after_a_frozen_lock():
    """RED without the backstop (decide() never emits a toward move at this spacing),
    GREEN with it: after ANTI_STALL_MAX frozen frames a toward-target key is injected."""
    c = AttackerController(attacker_num=1, level=5, rng=random.Random(0))
    p1, p2 = _frozen_pair()
    toward = p1.controls["right"]            # p2 is to p1's right
    fired_at = None
    for f in range(ANTI_STALL_MAX + 5):
        keys = c.decide(p1, p2, f)           # positions/percents frozen -> a lock
        if toward in keys:
            fired_at = f
            break
    assert fired_at is not None, "backstop never injected a toward-target action"
    assert fired_at >= ANTI_STALL_MAX, f"backstop fired too early (frame {fired_at})"
    # and it overrides any conflicting away-move (no left+right cancel)
    assert p1.controls["left"] not in c.decide(p1, p2, ANTI_STALL_MAX + 6)


def test_backstop_stays_silent_while_engaging():
    """Faithfulness guard (#376): a bot landing hits (target percent changing) never
    trips the backstop — engagement resets the no-progress counter every frame."""
    c = AttackerController(attacker_num=1, level=5, rng=random.Random(0))
    p1, p2 = _frozen_pair()
    for f in range(ANTI_STALL_MAX * 3):
        p2.fighter.percent += 1.0            # a hit lands each frame -> engagement
        c.decide(p1, p2, f)
    assert c._noprog < ANTI_STALL_MAX, "backstop tripped despite active engagement"


def test_backstop_stays_silent_while_moving():
    """Faithfulness guard: a bot that keeps traversing (> ANTI_STALL_MOVE_PX/frame)
    never trips — micro-movement / repositioning resets the reference."""
    c = AttackerController(attacker_num=1, level=5, rng=random.Random(0))
    p1, p2 = _frozen_pair()
    for f in range(ANTI_STALL_MAX * 3):
        p1.rect.x += (ANTI_STALL_MOVE_PX + 4) * (1 if f % 2 == 0 else -1)
        c.decide(p1, p2, f)
    assert c._noprog < ANTI_STALL_MAX, "backstop tripped despite the bot moving"


def test_level_less_default_never_arms_the_backstop():
    """Golden-safety: the level-less default path skips the detector entirely."""
    c = AttackerController(attacker_num=1)   # level=None
    p1, p2 = _frozen_pair()
    for f in range(ANTI_STALL_MAX + 5):
        c.decide(p1, p2, f)
    assert c._noprog == 0, "level-less default must not arm the anti-stall backstop"
