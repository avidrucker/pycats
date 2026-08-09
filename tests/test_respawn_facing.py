"""Regression tests for respawn facing reset (issue #7).

When a player is KO'd and respawns, their facing must return to that player's
*initial* direction (P1 faces right toward center, P2 faces left toward center)
regardless of which way they happened to be facing when KO'd. The fix lives in
``Player._respawn`` (restores ``original_facing_right``); these tests guard it
through the real per-frame ``update`` loop so the behavior cannot silently
regress.
"""

import pygame  # type: ignore
import pytest
from helpers import mk_player

from pycats.config import DEAD_FRAMES, REBIRTH_FRAMES, SCREEN_HEIGHT
from pycats.core.input import InputFrame
from pycats.entities.platform import Platform


def _noop():
    return InputFrame(held=set(), pressed=set(), released=set())


def _mk_player(initial_facing_right):
    p = mk_player(y=300, facing_right=initial_facing_right)
    p.fighter.lives = 3
    return p


@pytest.mark.parametrize("initial_facing_right", [True, False])
def test_respawn_restores_initial_facing(initial_facing_right):
    """A player KO'd while facing the opposite way respawns facing its initial direction."""
    p = _mk_player(initial_facing_right)
    platforms = [Platform(pygame.Rect(0, 340, 600, 40), thin=False)]
    p.platforms = platforms

    # Simulate the player having turned to face the *opposite* of its initial direction.
    p.fighter.facing_right = not initial_facing_right

    # Force a KO by driving the player out the bottom blast zone, via the real loop.
    p.rect = p.rect.with_top(SCREEN_HEIGHT + 9999)
    p.update(_noop(), platforms, pygame.sprite.Group())
    assert not p.fighter.is_alive, "precondition: player should be KO'd"
    # Facing is untouched while dead/waiting; the reset happens on respawn.
    assert p.fighter.facing_right == (not initial_facing_right)

    # Tick through the two-phase DEAD -> REBIRTH re-entry (#1334); begin_rebirth restores facing.
    for _ in range(DEAD_FRAMES + REBIRTH_FRAMES + 2):
        p.update(_noop(), platforms, pygame.sprite.Group())

    assert p.fighter.is_alive, "player should have respawned"
    assert p.fighter.facing_right == initial_facing_right, (
        "respawn did not reset facing to the player's initial direction"
    )
