"""A hit-stunned or shield-break-dizzy fighter must not *input* a soft-platform
drop-through by holding down (#612, PM parity).

`Player.update` gates walk/jump/dodge/attack on `in_hitstun`, but the held-`down`
drop-through read lives downstream in `step_physics` (`fighter_physics.py`), which
was ungated. #612 threads the hitstun timers into `should_prevent_drop_through`,
so a stunned fighter can't drop through a thin platform — matching PM/Melee, where
drop-through requires the standing/actionable state. The gate suppresses only the
held-`down` input path, not knockback trajectory.
"""

import pygame

from pycats.core.input import InputFrame
from pycats.entities import Player
from pycats.entities.platform import Platform

_CONTROLS = dict(
    left=pygame.K_a,
    right=pygame.K_d,
    up=pygame.K_w,
    down=pygame.K_s,
    attack=pygame.K_v,
    special=pygame.K_c,
    shield=pygame.K_x,
)


def _mk():
    return Player(100, 100, _CONTROLS, (255, 160, 64), eye_color=(0, 0, 0), char_name="P1", facing_right=True)


def _thin():
    # A thin (pass-through) platform below the spawn — the fighter falls onto it
    # and can normally drop through it by holding down.
    return [Platform(pygame.Rect(0, 300, 600, 20), thin=True)]


def _down():
    d = _CONTROLS["down"]
    return InputFrame(held={d}, pressed={d}, released=set())


def _neutral():
    return InputFrame(held=set(), pressed=set(), released=set())


def _land_on_thin(p, plats):
    grp = pygame.sprite.Group()
    for _ in range(120):
        p.update(_neutral(), plats, grp)
        if p.fighter.on_ground:
            return True
    return False


def test_actionable_fighter_drops_through_when_holding_down():
    # Control: a normal (non-stunned) fighter holding down on a thin platform DOES
    # drop through — proves the setup can observe a drop-through at all.
    p = _mk()
    plats = _thin()
    assert _land_on_thin(p, plats), "setup: fighter should land on the thin platform"
    grp = pygame.sprite.Group()
    for _ in range(5):
        p.update(_down(), plats, grp)
    assert not p.fighter.on_ground, "actionable fighter should drop through the thin platform"


def test_hitstun_fighter_does_not_drop_through_on_held_down():
    p = _mk()
    plats = _thin()
    assert _land_on_thin(p, plats)
    p.fighter.hurt_timer = 30  # in hitstun for the whole window below
    grp = pygame.sprite.Group()
    for _ in range(3):
        p.update(_down(), plats, grp)
    assert p.fighter.on_ground, "hit-stunned fighter must not drop through on held-down"


def test_dizzy_fighter_does_not_drop_through_on_held_down():
    p = _mk()
    plats = _thin()
    assert _land_on_thin(p, plats)
    p.fighter.stun_timer = 30  # shield-break dizzy for the whole window below
    grp = pygame.sprite.Group()
    for _ in range(3):
        p.update(_down(), plats, grp)
    assert p.fighter.on_ground, "dizzy fighter must not drop through on held-down"
