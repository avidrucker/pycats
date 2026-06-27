"""tests/test_shieldstun.py

Shieldstun on a blocked hit (#38 final slice, #140).

A shielded hit that the shield SURVIVES locks the defender in shield for
shieldstun_frames(damage) = floor(damage * 0.345) frames (SmashWiki / the project
roadmap), and both fighters take hitlag (the #138 shield-hitlag deferral).
Shield-BREAK still routes to the dizzy `stun`, not shieldstun.
"""
import pygame as pg

from pycats.entities.player import Player
from pycats.entities.attack import Attack
from pycats.entities.platform import Platform
from pycats.combat.shield import shieldstun_frames
from pycats.combat.knockback import hitlag_frames
from pycats.combat.data import Circle, Hitbox
from pycats.core.input import InputFrame

P1 = dict(left=pg.K_a, right=pg.K_d, up=pg.K_w, down=pg.K_s,
          attack=pg.K_v, special=pg.K_c, shield=pg.K_x)


def _mk(char="P1"):
    return Player(100, 100, P1, (255, 160, 64), eye_color=(0, 0, 0),
                  char_name=char, facing_right=True)


def _atk(owner, damage):
    hb = Hitbox(circle=Circle(dx=20, dy=30, r=14), damage=damage, angle=45,
                base_knockback=30.0, knockback_growth=100.0)
    return Attack(owner, hitbox=hb, lifetime=2)


def _shielding(p):
    p.fighter.on_ground = True
    p.fighter.shield_attempting = True
    p.engine.tick(None)
    assert p.state == "shield"
    return p


# ---- pure formula ---------------------------------------------------------

def test_shieldstun_frames_reference_values():
    assert shieldstun_frames(9) == 3     # floor(9 * 0.345)  = floor(3.105) = 3
    assert shieldstun_frames(12) == 4    # floor(12 * 0.345) = floor(4.14)  = 4
    assert shieldstun_frames(2) == 0     # < ~2.9% -> 0 (floor(0.69))


# ---- behaviour ------------------------------------------------------------

def test_blocked_hit_sets_shieldstun_and_hitlag_on_both():
    pg.init()
    attacker = _mk("A")
    defender = _shielding(_mk("D"))
    atk = _atk(attacker, 12)
    defender.fighter.receive_hit(atk)
    assert defender.fighter.shieldstun_timer == shieldstun_frames(12) == 4
    assert defender.fighter.hitlag_timer == hitlag_frames(12), "shield hitlag on defender"
    assert attacker.fighter.hitlag_timer == hitlag_frames(12), "shield hitlag on attacker"
    # a blocked (non-breaking) hit deals no percent and no dizzy stun
    assert defender.fighter.percent == 0
    assert defender.fighter.stun_timer == 0


def test_defender_locked_in_shield_during_shieldstun_then_freed():
    pg.init()
    attacker = _mk("A")
    defender = _shielding(_mk("D"))
    platforms = [Platform(pg.Rect(0, 160, 600, 40), thin=False)]
    grp = pg.sprite.Group()
    defender.fighter.receive_hit(_atk(attacker, 12))

    # Let any hitlag freeze elapse first (shieldstun runs after hitlag).
    while defender.fighter.hitlag_timer > 0:
        defender.update(InputFrame(held=set(), pressed=set(), released=set()), platforms, grp)

    ss = defender.fighter.shieldstun_timer
    assert ss > 0
    # During shieldstun: even pressing jump does nothing — locked in shield.
    jump = InputFrame(held=set(), pressed={P1["up"]}, released=set())
    for _ in range(ss):
        defender.update(jump, platforms, grp)
        assert defender.state == "shield", "defender must stay shielding during shieldstun"
    # Freed: now a jump press leaves the ground / shield.
    defender.update(jump, platforms, grp)
    assert defender.state != "shield", "defender should act once shieldstun ends"


def test_shield_break_still_routes_to_stun_not_shieldstun():
    pg.init()
    attacker = _mk("A")
    defender = _shielding(_mk("D"))
    defender.fighter.shield_hp = 5  # low enough that a 12% hit depletes it
    defender.fighter.receive_hit(_atk(attacker, 12))
    assert defender.fighter.stun_timer > 0, "a broken shield should dizzy-stun"
    assert defender.fighter.shieldstun_timer == 0, "broken shield -> stun, not shieldstun"
