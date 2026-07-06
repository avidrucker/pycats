"""Keybinding-set UI controller (#463) — the save / load / rename / delete flow.

Pure logic over `keybind_store` (#440) + a `TextEntry` (#471) + a set-list cursor,
driven by discrete method calls (the OptionsMenu adapter turns `pressed` into these).
Headless; the store writes under PYCATS_CONFIG_DIR (pointed at tmp_path, the #95 pattern).
"""


import pygame
import pytest

from pycats import keybind_store
from pycats.core.keymap import Keymap
from pycats.keybind_sets_menu import KeybindSetsMenu


@pytest.fixture(autouse=True)
def _tmp_config(tmp_path, monkeypatch):
    monkeypatch.setenv("PYCATS_CONFIG_DIR", str(tmp_path))


def _keymaps():
    p1 = Keymap(dict(attack=pygame.K_v, shield=pygame.K_x, left=pygame.K_a))
    p2 = Keymap(dict(attack=pygame.K_SLASH, shield=pygame.K_COMMA, left=pygame.K_LEFT))
    return [p1, p2]


def _type(menu, name):
    """Drive the active TextEntry to spell `name` then confirm (DONE)."""
    for ch in name.upper():
        menu.entry.cursor = menu.entry.cells.index(ch)
        menu.select()
    menu.entry.cursor = menu.entry.cells.index("DONE")
    menu.select()


def test_save_current_names_and_persists_the_focused_players_scheme():
    kms = _keymaps()
    menu = KeybindSetsMenu(kms)
    menu.open(0)                                   # focus P1
    menu.menu_index = menu.MENU.index("Save current...")
    menu.select()                                  # -> text entry
    assert menu.view == "text"
    _type(menu, "MINE")
    assert "MINE" in keybind_store.list_sets()     # persisted under the typed name
    assert menu.view == "menu"                     # returns to the menu after saving


def test_save_uses_the_focused_players_live_keymap():
    kms = _keymaps()
    kms[1]["attack"] = pygame.K_z                   # tweak P2 in memory before saving
    menu = KeybindSetsMenu(kms)
    menu.open(1)                                     # focus P2
    menu.menu_index = menu.MENU.index("Save current...")
    menu.select()
    _type(menu, "P2SET")
    fresh = Keymap(dict(attack=pygame.K_1, shield=pygame.K_2, left=pygame.K_3))
    loaded = keybind_store.load_set("P2SET", fresh)
    assert loaded["attack"] == pygame.K_z           # P2's live binding was saved, not P1's


def test_load_applies_a_saved_scheme_to_the_focused_player():
    kms = _keymaps()
    saved = Keymap(dict(attack=pygame.K_j, shield=pygame.K_k, left=pygame.K_l))
    keybind_store.save_set("loadme", saved)
    menu = KeybindSetsMenu(kms)
    menu.open(0)
    menu.menu_index = menu.MENU.index("Load...")
    menu.select()                                    # -> set list
    assert menu.view == "list" and menu.sets == ["loadme"]
    menu.select()                                    # pick the (only) set
    assert kms[0]["attack"] == pygame.K_j            # applied to P1's live keymap
    assert menu.view == "menu"


def test_rename_saves_under_the_new_name_and_drops_the_old():
    kms = _keymaps()
    keybind_store.save_set("old", kms[0])
    menu = KeybindSetsMenu(kms)
    menu.open(0)
    menu.menu_index = menu.MENU.index("Rename...")
    menu.select()                                    # -> list
    menu.select()                                    # pick "old" -> text entry
    assert menu.view == "text"
    _type(menu, "NEW")
    assert keybind_store.list_sets() == ["NEW"]      # old gone, new present


def test_delete_removes_the_scheme_after_a_confirm_step():
    kms = _keymaps()
    keybind_store.save_set("gone", kms[0])
    keybind_store.save_set("keep", kms[0])
    menu = KeybindSetsMenu(kms)
    menu.open(0)
    menu.menu_index = menu.MENU.index("Delete...")
    menu.select()                                    # -> list (["gone","keep"])
    menu.list_index = menu.sets.index("gone")
    menu.select()                                    # -> confirm
    assert menu.view == "confirm"
    menu.select()                                    # confirm the delete
    assert keybind_store.list_sets() == ["keep"]     # only "gone" removed
    assert menu.view == "menu"


def test_load_with_no_saved_schemes_stays_on_the_menu_with_a_message():
    menu = KeybindSetsMenu(_keymaps())
    menu.open(0)
    menu.menu_index = menu.MENU.index("Load...")
    menu.select()
    assert menu.view == "menu"                       # nothing to list
    assert menu.message == "no saved schemes"


def test_back_pops_a_subview_to_the_menu_then_signals_done():
    kms = _keymaps()
    keybind_store.save_set("x", kms[0])
    menu = KeybindSetsMenu(kms)
    menu.open(0)
    menu.menu_index = menu.MENU.index("Load...")
    menu.select()                                    # into the list sub-view
    menu.back()
    assert menu.view == "menu" and menu.done is False # first back returns to the menu
    menu.back()
    assert menu.done is True                          # second back leaves the sub-mode


def test_menu_nav_wraps_within_the_action_list():
    menu = KeybindSetsMenu(_keymaps())
    menu.open(0)
    menu.move(0, -1)                                  # up from the first row wraps to last
    assert menu.menu_index == len(menu.MENU) - 1
