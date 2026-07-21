"""tests/test_invincible_hit.py

The INVINCIBLE combat branch — "register but zero" (#802, decision #784).

When an attack connects with an INVINCIBLE defender the hit CONNECTS (contact is
made, unlike the INTANGIBLE pass-through) but the defender is "otherwise
unaffected": the ATTACKER takes hitlag (freezes), while the defender's percent,
knockback, hitstun, and hitlag are all zeroed. Grounded in the #797 findings
(docs/research/2026-07-20-pm-invincible-hitlag-findings.md, Q1/Q2/§6): meleelight
`executeRegularHit` sets the attacker's hitlag before bailing out of the invincible
victim's processing; SmashWiki (series-universal) — "the attacker will still
experience hitlag … the opponent will otherwise be unaffected." The PM-3.6 step is
`[inference]`; no PM primary exists.

Two layers:
  * `receive_hit_invincible` semantics — real Players (this file).
  * combat-gate routing (INVINCIBLE registers, does NOT take the damage path) —
    tests/test_combat.py.
"""

import pygame

from pycats.combat.data import Circle, Hitbox
from pycats.combat.knockback import hitlag_frames
from pycats.entities.attack import Attack
from pycats.entities.player import Player

P1 = dict(
    left=pygame.K_a,
    right=pygame.K_d,
    up=pygame.K_w,
    down=pygame.K_s,
    attack=pygame.K_v,
    special=pygame.K_c,
    shield=pygame.K_x,
)
P2 = dict(
    left=pygame.K_LEFT,
    right=pygame.K_RIGHT,
    up=pygame.K_UP,
    down=pygame.K_DOWN,
    attack=pygame.K_PERIOD,
    special=pygame.K_SLASH,
    shield=pygame.K_RSHIFT,
)


def _mk(char, x, facing):
    return Player(
        x, 100, P1 if facing else P2, (255, 160, 64), eye_color=(0, 0, 0), char_name=char, facing_right=facing
    )


def _hit(owner, damage):
    hb = Hitbox(circle=Circle(dx=20, dy=30, r=14), damage=damage, angle=45, base_knockback=30.0, knockback_growth=100.0)
    return Attack(owner, hitbox=hb, lifetime=2)


def test_receive_hit_invincible_freezes_only_the_attacker():
    pygame.init()
    attacker = _mk("P1", 100, True)
    defender = _mk("P2", 130, False)
    atk = _hit(attacker, 12)

    percent0 = defender.fighter.percent
    hurt0 = defender.fighter.hurt_timer

    defender.fighter.receive_hit_invincible(atk)

    # Attacker freezes for the normal hitlag duration (Q1).
    assert attacker.fighter.hitlag_timer == hitlag_frames(12), "attacker should freeze"
    # Invincible defender is "otherwise unaffected" (Q2 / §6): no hitlag, no damage,
    # no knockback launch, no hitstun.
    assert defender.fighter.hitlag_timer == 0, "invincible defender must NOT freeze"
    assert defender.fighter.percent == percent0, "invincible defender takes no damage"
    assert defender.fighter.vel.length() == 0, "invincible defender takes no knockback"
    assert defender.fighter.hurt_timer == hurt0, "invincible defender takes no hitstun"


def test_invincible_defender_does_not_take_the_normal_damage_path():
    # Revert-the-branch guard: if receive_hit_invincible were (wrongly) the normal
    # receive_hit, the defender's percent would rise by the hit's damage.
    pygame.init()
    attacker = _mk("P1", 100, True)
    defender = _mk("P2", 130, False)
    atk = _hit(attacker, 12)
    defender.fighter.receive_hit_invincible(atk)
    assert defender.fighter.percent == 0, "no percent applied to an invincible defender"
