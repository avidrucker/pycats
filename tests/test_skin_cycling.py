"""Char-select skin cycling — per-player OG-palette cycle wired into the match (#650, Part 3 of #127).

After a player confirms a character, left/right cycles its colour palette through the six
OG skins (wrap-around), per-player and independent; the chosen skin flows into the match via
`create_from_selection(..., p1_palette, p2_palette)`. With no cycling the default is the
archetype's own palette — byte-identical to before.
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

from pycats.battle_screen import BattleScreen  # noqa: E402
from pycats.char_select import CharacterSelector  # noqa: E402
from pycats.characters.roster import ARCHETYPE_DEFAULT_SKIN, palette_for  # noqa: E402

_P1 = {"left": 1, "right": 2, "up": 3, "down": 4, "attack": 5, "special": 6}
_P2 = {"left": 11, "right": 12, "up": 13, "down": 14, "attack": 15, "special": 16}


def _sel():
    pygame.init()
    return CharacterSelector(_P1, _P2)


def _confirm_p1(sel, char_index=0):
    sel.p1_cursor = char_index
    sel.p1_input_cooldown = 0
    sel.update(set(), {_P1["attack"]})


# ---- char-select cycling logic ------------------------------------------------


def test_confirm_initializes_palette_to_the_archetype_default():
    sel = _sel()
    _confirm_p1(sel, 0)  # cursor 0 = nalio
    assert sel.p1_confirmed
    assert sel.p1_palette == ARCHETYPE_DEFAULT_SKIN["nalio"]  # "calico"


def test_left_right_cycle_the_palette_with_wraparound():
    sel = _sel()
    _confirm_p1(sel, 0)
    keys = sel._palette_keys
    start = keys.index(sel.p1_palette)

    sel.p1_input_cooldown = 0
    sel.update(set(), {_P1["right"]})
    assert keys.index(sel.p1_palette) == (start + 1) % len(keys)

    sel.p1_input_cooldown = 0
    sel.update(set(), {_P1["left"]})
    assert keys.index(sel.p1_palette) == start

    # wrap: left from the first skin lands on the last
    sel.p1_palette = keys[0]
    sel.p1_input_cooldown = 0
    sel.update(set(), {_P1["left"]})
    assert sel.p1_palette == keys[-1]


def test_cancel_clears_the_palette():
    sel = _sel()
    _confirm_p1(sel, 0)
    sel.p1_input_cooldown = 0
    sel.update(set(), {_P1["special"]})
    assert not sel.p1_confirmed
    assert sel.p1_palette is None


def test_cycling_is_independent_per_player():
    sel = _sel()
    _confirm_p1(sel, 0)  # p1 confirms, p2 untouched
    p1p, p2p = sel.get_selected_palettes()
    assert p1p == "red-blue"  # nalio's base-theme default (#677)
    assert p2p is None


# ---- wiring into the match ----------------------------------------------------


def test_chosen_palette_colours_the_player():
    pygame.init()
    bs = BattleScreen(_P1, _P2)
    bs.create_from_selection("nalio", "birky", p1_palette="tabby")
    assert tuple(bs.player1.char_color[:3]) == tuple(palette_for("tabby")["color"][:3])


def test_default_palette_is_unchanged():
    pygame.init()
    bs = BattleScreen(_P1, _P2)
    bs.create_from_selection("nalio", "birky")  # no palette → archetype default
    assert tuple(bs.player1.char_color[:3]) == tuple(palette_for("nalio")["color"][:3])
