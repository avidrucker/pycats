"""Shared test helpers — the single home for the Player / control-map / ground
boilerplate that ~two dozen test files used to re-declare by hand.

Child 2 of the refactoring epic #833 (findings §8,
`docs/research/2026-07-21-codebase-refactoring-review-findings.md`): import
`P1` / `mk_player` / `ground` from here instead of copying them per file.
`tests/conftest.py` wraps these as the `p1_controls` / `p2_controls` / `player`
/ `ground` / `two_fighters` fixtures, so there is one source of truth.

`land_hit` and a golden-comparison util (named in the review) are intentionally
absent: the tree has no consistent duplication for them to collapse — the
hit-landing helper exists in two incompatible signatures across 4 files, and no
golden util is duplicated — so a shared version would be speculative dead code.
"""

import pygame

from pycats.entities.platform import Platform
from pycats.entities.player import Player

# Player-1 combat control map. 8-key superset: the shared shape carries `smash`
# so both the 7-key files (none of which press K_b) and the 5 smash-using files
# share one map with no behaviour change.
P1 = dict(
    left=pygame.K_a,
    right=pygame.K_d,
    up=pygame.K_w,
    down=pygame.K_s,
    attack=pygame.K_v,
    special=pygame.K_c,
    shield=pygame.K_x,
    smash=pygame.K_b,
)

# Player-2 combat control map (arrow cluster). Majority shape across files that
# define a P2; the few with swapped attack/special keep their local map.
P2 = dict(
    left=pygame.K_LEFT,
    right=pygame.K_RIGHT,
    up=pygame.K_UP,
    down=pygame.K_DOWN,
    attack=pygame.K_SLASH,
    special=pygame.K_PERIOD,
    shield=pygame.K_COMMA,
)

# The canonical hand-rolled colours (orange body, black eyes) every _mk_player used.
_COLOR = (255, 160, 64)
_EYE = (0, 0, 0)


def mk_player(x=100, y=100, controls=None, *, facing_right=True, char_name="P1", **kwargs):
    """Build a Player at the canonical spawn (100, 100) with the P1 map.

    Mirrors the per-file ``_mk_player()`` factories. ``controls`` defaults to
    ``P1``; extra kwargs (``fighter_data``, ``character``, …) pass through to
    ``Player``.
    """
    return Player(
        x,
        y,
        controls if controls is not None else P1,
        _COLOR,
        eye_color=_EYE,
        char_name=char_name,
        facing_right=facing_right,
        **kwargs,
    )


def ground(y=100, x=0, width=600, height=40, thin=False):
    """A wide solid platform under the canonical spawn (its top at y=100)."""
    return [Platform(pygame.Rect(x, y, width, height), thin=thin)]


def advance(player, frames, *args, **kwargs):
    """Tick ``player.update(*args, **kwargs)`` ``frames`` times; return the player."""
    for _ in range(frames):
        player.update(*args, **kwargs)
    return player
