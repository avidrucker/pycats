"""Regression tests for respawn clearing transient action timers (issue #31).

#9 made ``Player._respawn`` clear hurt_timer/stun_timer. #31 is the mirror for the
remaining transient action state: a player KO'd mid-dodge or mid-attack must not
carry dodge/attack/invulnerable timers (or the dodge/attack flags) into its next
life. ``_ko`` early-returns, so these never tick down during death — only the
respawn can clear them. Guards both state-engine backends through the real
per-frame ``update`` loop.
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


def _mk_player(backend):
    p = Player(100, 300, P1, (255, 160, 64), eye_color=(0, 0, 0),
               char_name="P1", facing_right=True, state_backend=backend)
    p.lives = 3
    return p


@pytest.mark.parametrize("backend", ["legacy", "statechart"])
def test_respawn_clears_transient_action_state(backend):
    """A player KO'd mid-dodge/mid-attack respawns with a clean transient slate."""
    p = _mk_player(backend)
    platforms = [Platform(pygame.Rect(0, 340, 600, 40), thin=False)]
    p.platforms = platforms

    # Force a KO out the bottom blast zone via the real loop.
    p.rect.top = SCREEN_HEIGHT + 9999
    p.update(_noop(), platforms, pygame.sprite.Group())
    assert not p.is_alive, "precondition: player should be KO'd"

    # _ko() early-returns, so transient action state set mid-dodge/mid-attack is
    # FROZEN through death (never ticks down). Replicate that frozen state now;
    # the dead-path of update() also early-returns, so nothing processes these
    # until _respawn runs. A live move clock (advanced a few frames) stands in
    # for mid-attack: current_move set, move_frame > 0, attack_timer > 0.
    p.dodge_timer = 20
    p.invulnerable_timer = 10
    p.invulnerable = True
    p.spot_dodge_shield_held = True
    p.dodge_blocked_by_edge = True
    p._clock.start(p.fighter_data.moves["attack"])
    for _ in range(7):
        p._clock.tick()
    p.done_attacking = False

    # Tick only until the respawn fires. The respawn frame early-returns, so we
    # assert on the freshly-respawned state without running another update (which
    # would process the stale move clock and mask whether _respawn cleared it).
    for _ in range(RESPAWN_DELAY_FRAMES + 5):
        if p.is_alive:
            break
        p.update(_noop(), platforms, pygame.sprite.Group())
    assert p.is_alive, "player should have respawned"

    assert p.dodge_timer == 0
    assert p.attack_timer == 0
    assert p.invulnerable_timer == 0
    assert p.invulnerable is False, "respawned permanently intangible (mid-dodge leak)"
    assert p.spot_dodge_shield_held is False
    assert p.dodge_blocked_by_edge is False
    assert p.current_move is None
    assert p.move_frame == 0
    assert p.done_attacking is True
