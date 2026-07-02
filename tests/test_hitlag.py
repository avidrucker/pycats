"""tests/test_hitlag.py

Hitlag / freeze frames on clean hits (#38 slice, #138).

A clean hit freezes BOTH the attacker and the defender for hitlag_frames(damage)
frames before the knockback slide. SmashWiki Hitlag (Brawl/PM):
    floor((d * 0.3846154 + 5) * h * e) * c, capped at 30
with h = e = c = 1 in this slice. Position, velocity, move-clock and the hitstun
timer are all held during the freeze, then resume intact.
"""
import math
import pygame

from pycats.combat.knockback import hitlag_frames
from pycats.entities.player import Player
from pycats.entities.attack import Attack
from pycats.entities.platform import Platform
from pycats.combat.data import Circle, Hitbox
from pycats.core.input import InputFrame

P1 = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w, down=pygame.K_s,
          attack=pygame.K_v, special=pygame.K_c, shield=pygame.K_x)
P2 = dict(left=pygame.K_LEFT, right=pygame.K_RIGHT, up=pygame.K_UP, down=pygame.K_DOWN,
          attack=pygame.K_PERIOD, special=pygame.K_SLASH, shield=pygame.K_RSHIFT)


# ---- pure formula ---------------------------------------------------------

def test_hitlag_frames_reference_values():
    assert hitlag_frames(9) == 8     # floor(9*0.3846154 + 5) = floor(8.46) = 8
    assert hitlag_frames(12) == 9    # floor(12*0.3846154 + 5) = floor(9.62) = 9
    assert hitlag_frames(0) == 5     # floor(5) = 5 (base only)


def test_hitlag_frames_capped_at_30():
    assert hitlag_frames(1000) == 30, "hitlag caps at 30 frames (Brawl onward)"


# ---- behaviour ------------------------------------------------------------

def _mk(char, x, facing):
    return Player(x, 100, P1 if facing else P2, (255, 160, 64),
                  eye_color=(0, 0, 0), char_name=char, facing_right=facing)


def _hit(owner, damage):
    hb = Hitbox(circle=Circle(dx=20, dy=30, r=14), damage=damage, angle=45,
                base_knockback=30.0, knockback_growth=100.0)
    return Attack(owner, hitbox=hb, lifetime=2)


def test_clean_hit_freezes_both_attacker_and_defender():
    pygame.init()
    attacker = _mk("P1", 100, True)
    defender = _mk("P2", 130, False)
    atk = _hit(attacker, 12)
    defender.fighter.receive_hit(atk)
    hl = hitlag_frames(12)
    assert defender.fighter.hitlag_timer == hl, "defender should freeze"
    assert attacker.fighter.hitlag_timer == hl, "attacker should freeze too"


def test_position_and_hitstun_held_during_freeze_then_resume():
    pygame.init()
    attacker = _mk("P1", 100, True)
    defender = _mk("P2", 200, False)
    platforms = [Platform(pygame.Rect(0, 160, 600, 40), thin=False)]
    grp = pygame.sprite.Group()

    atk = _hit(attacker, 12)
    defender.fighter.receive_hit(atk)
    hl = hitlag_frames(12)
    assert defender.fighter.vel.length() > 0, "launch velocity is set at hit time"

    x0 = defender.rect.x
    hurt0 = defender.fighter.hurt_timer
    noop = InputFrame(held=set(), pressed=set(), released=set())

    # During the freeze: position and hitstun timer are held.
    for f in range(hl):
        defender.update(noop, platforms, grp)
        assert defender.rect.x == x0, f"defender should not move during hitlag (frame {f})"
        assert defender.fighter.hurt_timer == hurt0, "hitstun must not tick during hitlag"
        assert defender.fighter.hitlag_timer == hl - 1 - f

    # Freeze over: now the knockback slide moves it and hitstun ticks down.
    defender.update(noop, platforms, grp)
    assert defender.rect.x != x0, "defender should move once hitlag ends (knockback)"
