"""Char-select live skin preview — the Character **grid tile itself** recolors to the
cycled Skin (#676, revisiting #662/#650).

#662 drew a separate recolored preview cat *outside* the grid (`_confirmation_preview_pos`).
#676 retires that: the grid tile paints in the selecting player's cycled Skin in place, and
the FCFS per-Character Skin lock (#755) keeps two players on one Character distinct — so a
single shared tile can show the most-recently-active player's Skin without a clash. Each
player's own held Skin is also surfaced by their P1..P4 slot (#682, tested separately).
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

from pycats.char_select import CharacterSelector  # noqa: E402
from pycats.characters.roster import palette_for  # noqa: E402

_P1 = {"left": 1, "right": 2, "up": 3, "down": 4, "attack": 5, "special": 6}
_P2 = {"left": 11, "right": 12, "up": 13, "down": 14, "attack": 15, "special": 16}


def _sel():
    pygame.init()
    return CharacterSelector(_P1, _P2)


def _confirm_p1(sel, char_index=0):
    sel.p1_cursor = char_index
    sel.p1_input_cooldown = 0
    sel.update(set(), {_P1["attack"]})


def _confirm_p2(sel, char_index=0):
    sel.p2_cursor = char_index
    sel.p2_input_cooldown = 0
    sel.update(set(), {_P2["attack"]})


def _cycle_p1(sel, direction="right"):
    sel.p1_input_cooldown = 0
    sel.update(set(), {_P1[direction]})


def _cycle_p1_to(sel, skin_key):
    for _ in range(20):
        if sel.p1_palette == skin_key:
            return
        _cycle_p1(sel, "right")
    raise AssertionError(f"never cycled to {skin_key}; stuck at {sel.p1_palette}")


def _color(skin_key):
    return tuple(palette_for(skin_key)["color"])


def _tile_body(sel, screen, char_pos):
    """RGB at the body centre of the grid tile at ``char_pos``."""
    from pycats.config import CHAR_SELECT_TILE_SIZE

    x, y = sel._grid_pos_to_screen_pos(char_pos)
    return screen.get_at((x + CHAR_SELECT_TILE_SIZE // 2, y + CHAR_SELECT_TILE_SIZE // 2))[:3]


def test_confirmed_grid_tile_recolors_to_the_cycled_skin():
    # Confirm P1 on nalio, cycle to void (20,20,20) — a colour nothing else on the tile
    # shares — and the grid TILE itself must paint in the chosen Skin. Able-to-fail: red if
    # the grid loop draws the Character default instead of the player's cycled Skin.
    sel = _sel()
    _confirm_p1(sel, 0)  # nalio
    _cycle_p1_to(sel, "void")

    screen = pygame.Surface((960, 540))
    sel.render(screen)

    char_pos = sel.characters.index("nalio")
    body = _tile_body(sel, screen, char_pos)
    assert body == _color("void"), body
    assert body != _color("nalio")  # not the Character default


def test_unconfirmed_tile_keeps_the_character_default_skin():
    # A tile no player has confirmed shows the Character's own default palette, unchanged.
    sel = _sel()
    screen = pygame.Surface((960, 540))
    sel.render(screen)
    char_pos = sel.characters.index("narz")
    assert _tile_body(sel, screen, char_pos) == _color("narz")


def test_shared_grid_tile_follows_the_last_active_player():
    # Two players on nalio (FCFS keeps them distinct). The shared tile paints the last
    # player to act on it — asserted on `_active_skin_by_char`, the state the grid loop
    # reads. (A pixel read is confounded once both confirm, when the start overlay opens.)
    sel = _sel()
    _confirm_p1(sel, 0)  # only P1 on nalio → tile shows P1's Skin
    assert sel._active_skin_by_char["nalio"] == sel.p1_palette
    _confirm_p2(sel, 0)  # P2 joins nalio, de-collided → tile now shows the last confirmer, P2
    assert sel._active_skin_by_char["nalio"] == sel.p2_palette
    assert sel.p1_palette != sel.p2_palette  # FCFS: distinct Skins


def test_releasing_a_shared_tile_hands_it_back_to_the_remaining_player():
    # Both on nalio (tile → P2). P2 backs out of the start overlay → the tile reverts to the
    # still-confirmed P1's Skin rather than keeping P2's stale entry (#676).
    sel = _sel()
    _confirm_p1(sel, 0)
    _confirm_p2(sel, 0)  # both confirmed → start overlay opens
    sel.p2_input_cooldown = 0
    sel.update(set(), {_P2["special"]})  # P2 presses back
    assert sel._active_skin_by_char["nalio"] == sel.p1_palette


def test_external_preview_cat_is_retired():
    # #676: the separate recolored preview cat drawn outside the grid is gone.
    sel = _sel()
    assert not hasattr(sel, "_confirmation_preview_pos")
