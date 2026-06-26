"""Regression tests for respawn facing reset (issue #7).

When a player is KO'd and respawns, their facing must return to that player's
*initial* direction (P1 faces right toward center, P2 faces left toward center)
regardless of which way they happened to be facing when KO'd. The fix lives in
``Player._respawn`` (restores ``original_facing_right``); these tests guard it on
both state-engine backends through the real per-frame ``update`` loop so the
behavior cannot silently regress.
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # type: ignore
import pytest

from pycats.entities.player import Player
from pycats.entities.platform import Platform
from pycats.core.input import InputFrame
from pycats.config import RESPAWN_DELAY_FRAMES, SCREEN_HEIGHT

P1 = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w, down=pygame.K_s,
          attack=pygame.K_v, special=pygame.K_c, shield=pygame.K_x)


def _noop():
    return InputFrame(held=set(), pressed=set(), released=set())


def _mk_player(initial_facing_right, backend):
    p = Player(100, 300, P1, (255, 160, 64), eye_color=(0, 0, 0),
               char_name="P1", facing_right=initial_facing_right,
               state_backend=backend)
    p.fighter.lives = 3
    return p


@pytest.mark.parametrize("backend", ["legacy", "statechart"])
@pytest.mark.parametrize("initial_facing_right", [True, False])
def test_respawn_restores_initial_facing(initial_facing_right, backend):
    """A player KO'd while facing the opposite way respawns facing its initial direction."""
    p = _mk_player(initial_facing_right, backend)
    platforms = [Platform(pygame.Rect(0, 340, 600, 40), thin=False)]
    p.platforms = platforms

    # Simulate the player having turned to face the *opposite* of its initial direction.
    p.fighter.facing_right = not initial_facing_right

    # Force a KO by driving the player out the bottom blast zone, via the real loop.
    p.rect.top = SCREEN_HEIGHT + 9999
    p.update(_noop(), platforms, pygame.sprite.Group())
    assert not p.fighter.is_alive, "precondition: player should be KO'd"
    # Facing is untouched while dead/waiting; the reset happens on respawn.
    assert p.fighter.facing_right == (not initial_facing_right)

    # Tick through the respawn delay; _respawn fires from update() on both backends.
    for _ in range(RESPAWN_DELAY_FRAMES + 2):
        p.update(_noop(), platforms, pygame.sprite.Group())

    assert p.fighter.is_alive, "player should have respawned"
    assert p.fighter.facing_right == initial_facing_right, (
        "respawn did not reset facing to the player's initial direction"
    )
