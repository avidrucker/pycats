"""Jab reach + facing-correct hit geometry (#64).

A grounded jab must connect a body-adjacent (flush) opponent — and the result
must NOT depend on which way the *defender* faces (a fighter's body/hurtbox is
the same when it turns around). Before the fix, a defender facing AWAY (its
hurtbox correctly at body-center) was unreachable, while a defender facing TOWARD
the attacker was hittable only because `resolve_circle` mis-placed its hurtbox
off-body toward the attacker. Both must connect now.
"""
import pygame as pg

from pycats.entities.player import Player
from pycats.entities.platform import Platform
from pycats.entities.attack import Attack
from pycats.systems import combat
from pycats.config import P1_COLOR, P2_COLOR, WHITE

P1K = {"left": pg.K_a, "right": pg.K_d, "up": pg.K_w,
       "down": pg.K_s, "shield": pg.K_x, "attack": pg.K_v}
P2K = {"left": pg.K_LEFT, "right": pg.K_RIGHT, "up": pg.K_UP,
       "down": pg.K_DOWN, "shield": pg.K_COMMA, "attack": pg.K_SLASH}


def _jab_lands_on_flush_defender(defender_facing_right):
    """Attacker (facing right) flush against a defender on its right; spawn the
    real jab and run hit detection. Returns the damage P2 took."""
    attacker = Player(x=400, y=340, controls=P1K, color=P1_COLOR, eye_color=WHITE,
                      char_name="A", facing_right=True)
    defender = Player(x=460, y=340, controls=P2K, color=P2_COLOR, eye_color=WHITE,
                      char_name="D", facing_right=defender_facing_right)
    # Place them flush at the settled push gap (rect.x 41 apart, bodies touching+).
    attacker.rect.x, attacker.rect.y = 400, 340
    defender.rect.x, defender.rect.y = 441, 340
    attacker.facing_right = True
    defender.facing_right = defender_facing_right

    jab = attacker.fighter_data.moves["attack"].hitboxes[0]
    attacks = pg.sprite.Group()
    attacks.add(Attack(attacker, hitbox=jab, lifetime=3))
    combat.process_hits([attacker, defender], attacks)
    return defender.percent


def test_jab_connects_flush_defender_facing_toward_attacker():
    assert _jab_lands_on_flush_defender(defender_facing_right=False) > 0


def test_jab_connects_flush_defender_facing_away_from_attacker():
    """The #60 case: a fleeing defender faces away; its body-center hurtbox must
    still be reachable. RED before the reach+facing fix."""
    assert _jab_lands_on_flush_defender(defender_facing_right=True) > 0
