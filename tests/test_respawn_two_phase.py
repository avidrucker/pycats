"""Falsifiable regression for the two-phase DEAD -> REBIRTH KO re-entry (#1334,
epic #1316 child-3 slice 1).

Replaces the single ~2 s invisible freeze (`RESPAWN_DELAY_FRAMES`) with:
  1. a DEAD phase (`DEAD_FRAMES`) — off-screen / "gone", uncontrollable, no platform;
  2. a REBIRTH phase — the fighter is alive again ON a floating revival platform that
     appears top-centre, descends into place, and auto-vanishes after
     `REVIVAL_PLATFORM_VANISH_FRAMES` of inaction.

Red without the slice: the pre-slice single-freeze path flips `is_alive` back at
`RESPAWN_DELAY_FRAMES` (120 f) and never creates a `respawn_platform`, so the
platform assertions fail (and `Fighter.respawn_platform` did not exist).

Drives the real per-frame `Player.update` loop. The revival platform is woven back
into the platform list each frame here by hand — in production `sim/runner` and
`screens/battle_screen` weave it via `entities.respawn_platform.active_platforms`.
"""

import pygame  # type: ignore
from helpers import mk_player

from pycats.config import (
    DEAD_FRAMES,
    REBIRTH_FRAMES,
    REVIVAL_PLATFORM_VANISH_FRAMES,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from pycats.core.geometry import FrozenRect
from pycats.core.input import InputFrame
from pycats.entities.platform import Platform


def _noop():
    return InputFrame(held=set(), pressed=set(), released=set())


def _mk_player():
    p = mk_player(y=300)
    p.fighter.lives = 3
    return p


def _weave(base, p):
    """Stage platforms plus the fighter's live revival platform (mimics the
    production weave so the descent/stand collision resolves in this direct loop)."""
    plat = p.fighter.respawn_platform
    return list(base) + ([plat] if plat is not None else [])


def _ko(p, base):
    """KO the fighter out the bottom blast zone through the real loop."""
    p.rect = p.rect.with_top(SCREEN_HEIGHT + 9999)
    p.update(_noop(), base, pygame.sprite.Group())
    assert not p.fighter.is_alive, "precondition: player should be KO'd"


def test_dead_phase_is_offscreen_with_no_platform():
    """During DEAD the fighter is not alive and there is no revival platform yet."""
    p = _mk_player()
    base = [Platform(FrozenRect(0, 340, 600, 40), thin=False)]
    _ko(p, base)

    # The KO frame set the DEAD countdown; step through DEAD (short of its end).
    for _ in range(DEAD_FRAMES - 1):
        assert not p.fighter.is_alive, "still DEAD during the off-screen phase"
        assert p.fighter.respawn_platform is None, "no revival platform during DEAD"
        p.update(_noop(), _weave(base, p), pygame.sprite.Group())


def test_rebirth_spawns_a_topcentre_passthrough_platform_not_a_single_freeze():
    """At the end of DEAD the fighter is alive again ON a thin, top-centre revival
    platform — the distinguishing behaviour the single 120 f freeze never produced."""
    p = _mk_player()
    base = [Platform(FrozenRect(0, 340, 600, 40), thin=False)]
    _ko(p, base)

    # Step DEAD_FRAMES dead-frames: is_alive flips at DEAD_FRAMES, not 120.
    for _ in range(DEAD_FRAMES):
        p.update(_noop(), _weave(base, p), pygame.sprite.Group())

    assert p.fighter.is_alive, "REBIRTH: alive again after exactly DEAD_FRAMES (not 120)"
    plat = p.fighter.respawn_platform
    assert plat is not None, "REBIRTH spawns a revival platform"
    assert isinstance(plat, Platform)
    assert plat.thin, "the revival platform is pass-through / drop-through (thin)"
    assert plat.rect.centerx == SCREEN_WIDTH // 2, "revival platform is horizontally centred"
    assert plat.rect.centery < SCREEN_HEIGHT // 2, "revival platform floats in the upper half (top-centre)"
    # The fighter rides it: standing on top, centred over the platform.
    assert abs(p.rect.bottom - plat.rect.top) <= 2, "fighter stands on the revival platform"


def test_revival_platform_auto_vanishes_after_the_vanish_window():
    """Left alone, the revival platform disappears after REVIVAL_PLATFORM_VANISH_FRAMES."""
    p = _mk_player()
    base = [Platform(FrozenRect(0, 340, 600, 40), thin=False)]
    _ko(p, base)
    for _ in range(DEAD_FRAMES):
        p.update(_noop(), _weave(base, p), pygame.sprite.Group())
    assert p.fighter.respawn_platform is not None, "precondition: in REBIRTH with a platform"

    # Well before the vanish window it is still present.
    for _ in range(REVIVAL_PLATFORM_VANISH_FRAMES // 2):
        p.update(_noop(), _weave(base, p), pygame.sprite.Group())
    assert p.fighter.respawn_platform is not None, "platform persists mid-window"

    # Past the vanish window it is gone.
    for _ in range(REVIVAL_PLATFORM_VANISH_FRAMES // 2 + REBIRTH_FRAMES + 5):
        p.update(_noop(), _weave(base, p), pygame.sprite.Group())
    assert p.fighter.respawn_platform is None, "revival platform auto-vanished after its window"
