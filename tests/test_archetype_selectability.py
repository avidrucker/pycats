"""Archetype selectability — char-select offers the real roster + threads the chosen
fighter to the Player (#268, completes #127 Part 1).

The char-select roster is the implemented PM-archetypes (not the OG colour-skins), and
the selected key reaches load_fighter_data via Player(fighter_data=...) — while
char_name stays "P1"/"P2" so win-attribution + name rendering are unchanged.
"""

import pygame

from pycats.battle_screen import BattleScreen
from pycats.char_select import CharacterSelector
from pycats.characters.roster import ARCHETYPE_PALETTE, ARCHETYPE_ROSTER
from pycats.combat.data import load_fighter_data

_P1 = dict(
    left=pygame.K_a,
    right=pygame.K_d,
    up=pygame.K_w,
    down=pygame.K_s,
    attack=pygame.K_v,
    special=pygame.K_c,
    shield=pygame.K_x,
)
_P2 = dict(
    left=pygame.K_LEFT,
    right=pygame.K_RIGHT,
    up=pygame.K_UP,
    down=pygame.K_DOWN,
    attack=pygame.K_PERIOD,
    special=pygame.K_SLASH,
    shield=pygame.K_RSHIFT,
)


def test_char_select_roster_is_the_implemented_archetypes():
    cs = CharacterSelector(_P1, _P2)
    assert list(cs.characters) == ["nalio", "birky", "narz", "gnok"]  # +gnok (#821 slice 1)
    assert tuple(cs.characters) == ARCHETYPE_ROSTER


def test_create_from_selection_threads_the_chosen_fighter_data():
    bs = BattleScreen(_P1, _P2)
    bs.create_from_selection("nalio", "birky")
    assert bs.player1.fighter_data == load_fighter_data("nalio")  # JSON-backed (#851): equal, not identical
    assert bs.player2.fighter_data == load_fighter_data("birky")  # JSON-backed (#856): equal, not identical
    # label unchanged → win-attribution (stats_print) + name render stay intact
    assert bs.player1.char_name == "P1" and bs.player2.char_name == "P2"


def test_create_from_selection_uses_each_archetype_default_palette():
    bs = BattleScreen(_P1, _P2)
    bs.create_from_selection("nalio", "birky")
    assert bs.player1.char_color == ARCHETYPE_PALETTE["nalio"]["color"]
    assert bs.player2.char_color == ARCHETYPE_PALETTE["birky"]["color"]
    assert bs.player1.eye_color == ARCHETYPE_PALETTE["nalio"]["eye_color"]
