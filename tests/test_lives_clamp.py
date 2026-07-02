"""Regression test for #54 — Player._ko() must clamp lives at 0.

`_ko` decremented `self.lives` with no lower bound. The `lives >= 0` invariant
held only emergently (the real loop never re-KOs a 0-life player via the
`is_alive` + `lives > 0` gates). This pins the invariant at the mutation site so
it survives future callers that might KO a dead/zero-life player.

Revert check: remove the `max(0, ...)` clamp in `_ko` and
`test_ko_at_zero_lives_does_not_underflow` goes red (lives == -1).
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # type: ignore

from pycats.entities.player import Player
from pycats.config import P1_COLOR, WHITE, INITIAL_LIVES

pygame.init()

CONTROLS = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w,
                down=pygame.K_s, shield=pygame.K_q, attack=pygame.K_e)


def _player():
    return Player(x=420, y=400, controls=CONTROLS, color=P1_COLOR,
                  eye_color=WHITE, char_name="P", facing_right=True)


def test_ko_at_zero_lives_does_not_underflow():
    """The invariant: a KO at 0 lives leaves lives at 0, never negative."""
    p = _player()
    p.fighter.lives = 0
    p.fighter._ko()
    assert p.fighter.lives == 0


def test_normal_ko_still_decrements():
    """Guard against over-clamping: a KO above 0 still costs one life."""
    p = _player()
    assert p.fighter.lives == INITIAL_LIVES
    p.fighter._ko()
    assert p.fighter.lives == INITIAL_LIVES - 1
