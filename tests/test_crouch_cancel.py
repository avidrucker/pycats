"""Crouch-cancel (#135, follow-up to #124).

Project M / Melee's signature use of crouch: taking a hit *while crouching*
reduces the knockback dealt to you (the "c" crouch-cancel factor, 0.67x in
Melee/PM), making crouch a defensive tool. Before #135, a hit taken in the
`crouch` state dealt FULL knockback — `Fighter.receive_hit` had no crouch
awareness.

These tests drive a real crouch, then strike the defender directly via
`receive_hit` (bypassing geometry so the hit always lands, isolating the
knockback scaling from the crouch-lowered hurtbox of #124). The crouching
defender must be launched CROUCH_CANCEL_FACTOR x as far / fast as a standing
one struck by the identical hit.
"""
from types import SimpleNamespace

import pygame
import pytest

from pycats.entities import Player
from pycats.entities.platform import Platform
from pycats.core.input import InputFrame
from pycats.config import CROUCH_CANCEL_FACTOR

_CONTROLS = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w,
                 down=pygame.K_s, attack=pygame.K_v, special=pygame.K_c,
                 shield=pygame.K_x)


def _mk():
    return Player(100, 100, _CONTROLS, (255, 160, 64), eye_color=(0, 0, 0),
                  char_name="P", facing_right=True)


def _ground():
    return [Platform(pygame.Rect(0, 100, 600, 40), thin=False)]


def _frame(*keys):
    ks = {_CONTROLS[k] for k in keys}
    return InputFrame(held=set(ks), pressed=set(ks), released=set())


def _settle(p, plats, n=3):
    grp = pygame.sprite.Group()
    for _ in range(n):
        p.update(_frame(), plats, grp)


def _run(p, plats, frame, n=3):
    grp = pygame.sprite.Group()
    for _ in range(n):
        p.update(frame, plats, grp)


def _atk(attacker, damage=10.0, bkb=30.0, kbg=100.0, angle=0):
    # A horizontal (+x) hit with real BKB/KBG so the launch is non-zero. Only the
    # fields receive_hit reads are populated.
    return SimpleNamespace(owner=attacker, damage=damage, base_knockback=bkb,
                           knockback_growth=kbg, angle=angle)


def _struck_launch(crouching: bool):
    """Strike a settled defender (optionally crouching) and return (vel_x, hurt)."""
    plats = _ground()
    attacker = _mk(); _settle(attacker, plats)
    defender = _mk(); _settle(defender, plats)
    if crouching:
        _run(defender, plats, _frame("down"))
        assert defender.state == "crouch"
    else:
        assert defender.state == "idle"
    defender.fighter.vel.x = 0.0  # determinism: launch is the only horizontal source
    defender.fighter.receive_hit(_atk(attacker))
    return defender.fighter.vel.x, defender.fighter.hurt_timer


def test_crouching_defender_takes_reduced_knockback():
    """A crouching defender is launched CROUCH_CANCEL_FACTOR x a standing one."""
    stand_vx, _ = _struck_launch(crouching=False)
    crouch_vx, _ = _struck_launch(crouching=True)
    assert stand_vx > 0, "standing hit should launch the defender (sanity)"
    assert crouch_vx == pytest.approx(stand_vx * CROUCH_CANCEL_FACTOR)
    assert crouch_vx < stand_vx, "crouch-cancel must REDUCE knockback"


def test_crouch_cancel_also_shortens_hitstun():
    """Reduced knockback feeds reduced hitstun (hurt_timer) too."""
    _, stand_hurt = _struck_launch(crouching=False)
    _, crouch_hurt = _struck_launch(crouching=True)
    assert crouch_hurt <= stand_hurt
    assert crouch_hurt < stand_hurt, "lower KB should floor to fewer hitstun frames"


def test_crouch_cancel_factor_is_pm_starting_value():
    """The factor is the Melee/PM crouch-cancel multiplier (tuning start ~0.67)."""
    assert 0.6 <= CROUCH_CANCEL_FACTOR <= 0.75
