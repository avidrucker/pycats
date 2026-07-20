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
from pycats.domain import available_skins, character_for  # noqa: E402

_P1 = {"left": 1, "right": 2, "up": 3, "down": 4, "attack": 5, "special": 6}
_P2 = {"left": 11, "right": 12, "up": 13, "down": 14, "attack": 15, "special": 16}


def _sel():
    pygame.init()
    return CharacterSelector(_P1, _P2)


def _pool(char_key):
    """The per-Character skin pool (#755): shared OG six + that Character's own theme(s)."""
    return [s.key for s in available_skins(character_for(char_key))]


def _confirm_p1(sel, char_index=0):
    sel.p1_cursor = char_index
    sel.p1_input_cooldown = 0
    sel.update(set(), {_P1["attack"]})


def _confirm_p2(sel, char_index=1):
    sel.p2_cursor = char_index
    sel.p2_input_cooldown = 0
    sel.update(set(), {_P2["attack"]})


def _cycle_p1(sel, direction="right"):
    sel.p1_input_cooldown = 0
    sel.update(set(), {_P1[direction]})


def _cycle_p2(sel, direction="right"):
    sel.p2_input_cooldown = 0
    sel.update(set(), {_P2[direction]})


# ---- char-select cycling logic ------------------------------------------------


def test_confirm_initializes_palette_to_the_archetype_default():
    sel = _sel()
    _confirm_p1(sel, 0)  # cursor 0 = nalio
    assert sel.p1_confirmed
    assert sel.p1_palette == ARCHETYPE_DEFAULT_SKIN["nalio"]  # "red-blue"


def test_left_right_cycle_the_palette_with_wraparound():
    sel = _sel()
    _confirm_p1(sel, 0)  # nalio
    keys = _pool("nalio")
    start = keys.index(sel.p1_palette)

    _cycle_p1(sel, "right")
    assert keys.index(sel.p1_palette) == (start + 1) % len(keys)

    _cycle_p1(sel, "left")
    assert keys.index(sel.p1_palette) == start

    # wrap: left from the first skin lands on the last
    sel.p1_palette = keys[0]
    _cycle_p1(sel, "left")
    assert sel.p1_palette == keys[-1]


def test_cycle_pool_is_per_character_not_the_global_skin_set():
    # #676/#755: a player cycles only within their Character's pool (shared OG six + that
    # Character's own theme), never into another Character's base theme. Able-to-fail:
    # today `_palette_keys` is the global `load_palettes()` set, so nalio could cycle into
    # narz's `blue-black` / birky's `pink-red`.
    sel = _sel()
    _confirm_p1(sel, 0)  # nalio
    seen = set()
    for _ in range(len(_pool("nalio")) + 2):  # more than a full lap → whole pool
        seen.add(sel.p1_palette)
        _cycle_p1(sel, "right")
    assert seen == set(_pool("nalio"))
    assert "blue-black" not in seen  # narz's theme — never reachable from nalio
    assert "pink-red" not in seen  # birky's theme


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


# ---- FCFS per-Character skin lock (#676/#755) ---------------------------------


def test_same_character_second_player_gets_a_distinct_default_skin():
    # Both pick nalio. P1 holds the default (red-blue); P2's confirm must NOT land on the
    # same skin — it de-collides to the next available in nalio's pool (FCFS lock).
    sel = _sel()
    _confirm_p1(sel, 0)  # nalio -> red-blue
    _confirm_p2(sel, 0)  # nalio -> must differ
    assert sel.p1_palette == "red-blue"
    assert sel.p2_palette != sel.p1_palette


def test_cannot_cycle_onto_the_other_players_held_skin():
    # Both on nalio; P1 holds red-blue. P2 cycling a full lap must never rest on red-blue
    # and must always stay distinct from P1.
    sel = _sel()
    _confirm_p1(sel, 0)
    _confirm_p2(sel, 0)
    for _ in range(len(_pool("nalio")) + 2):
        assert sel.p2_palette != sel.p1_palette
        assert sel.p2_palette != "red-blue"  # P1's locked skin is skipped
        _cycle_p2(sel, "right")


def test_different_characters_share_no_lock():
    # P1 nalio, P2 narz — independent pools; each keeps its own default, no interaction.
    sel = _sel()
    _confirm_p1(sel, 0)  # nalio -> red-blue
    _confirm_p2(sel, 2)  # narz -> blue-black
    assert sel.p1_palette == "red-blue"
    assert sel.p2_palette == "blue-black"


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
