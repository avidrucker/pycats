"""OptionsMenu keybinding-schemes wiring (#463) — the adapter over KeybindSetsMenu.

The keybind screen (#455) gains a trailing "Schemes…" row that opens a save / load /
rename / delete sub-mode over `keybind_store` (#440). This drives OptionsMenu.update
with synthetic `pressed` sets and asserts the sub-mode + persistence react. Headless;
the store writes under PYCATS_CONFIG_DIR (tmp_path).
"""


import pygame
import pytest

from pycats import keybind_store
from pycats.core.keymap import Keymap
from pycats.options_menu import OptionsMenu

_P1 = {"up": 1, "down": 2, "left": 3, "right": 4, "attack": 5, "special": 6, "shield": 7}
_P2 = {"up": 11, "down": 12, "left": 13, "right": 14, "attack": 15, "special": 16, "shield": 17}


@pytest.fixture(autouse=True)
def _tmp_config(tmp_path, monkeypatch):
    monkeypatch.setenv("PYCATS_CONFIG_DIR", str(tmp_path))


def _options():
    p1, p2 = Keymap(dict(_P1)), Keymap(dict(_P2))
    return OptionsMenu(p1, p2), p1, p2


def _enter_keybind(om):
    om.keybind_mode = True
    om.keybind.player = 0
    om.keybind.action_index = 0
    om.keybind_on_schemes = False


def test_up_from_the_first_action_lands_on_the_schemes_row():
    om, _p1, _p2 = _options()
    _enter_keybind(om)
    om.update({1})                       # 'up' from action 0 -> the trailing Schemes row
    assert om.keybind_on_schemes is True


def test_activating_the_schemes_row_opens_the_sets_submode():
    om, _p1, _p2 = _options()
    _enter_keybind(om)
    om.keybind_on_schemes = True
    om.update({5})                       # 'attack' on the Schemes row -> open sets menu
    assert om.sets_mode is True
    assert om.sets.view == "menu"
    assert om.sets.player == 0           # opened for the keybind screen's focused player


def test_sets_back_returns_to_keybind_then_a_second_back_exits():
    om, _p1, _p2 = _options()
    _enter_keybind(om)
    om.keybind_on_schemes = True
    om.update({5})                       # open sets
    assert om.sets_mode is True
    om.input_cooldown = 0
    om.update({6})                       # 'special' -> back out of sets to the keybind screen
    assert om.sets_mode is False
    assert om.keybind_mode is True
    om.input_cooldown = 0
    om.update({6})                       # 'special' again -> leave the keybind screen
    assert om.keybind_mode is False


def test_saving_through_the_ui_captures_the_live_rebound_keymap():
    om, p1, _p2 = _options()
    p1["attack"] = 99                    # a remap made on the keybind screen (shared Keymap)
    _enter_keybind(om)
    om.keybind_on_schemes = True
    om.update({5})                       # open sets (focus P1)
    # Drive the sets controller to save under a name (grid typing is covered elsewhere).
    om.sets.menu_index = om.sets.MENU.index("Save current...")
    om.sets.select()
    om.sets.entry.cursor = om.sets.entry.cells.index("A")
    om.sets.select()
    om.sets.entry.cursor = om.sets.entry.cells.index("DONE")
    om.sets.select()
    fresh = Keymap(dict(_P1))
    assert keybind_store.load_set("A", fresh)["attack"] == 99   # saved the live P1 keymap


def test_sets_views_render_without_error():
    pygame.init()
    from pycats.config import MAIN_MENU_BG_COLOR, SCREEN_HEIGHT, SCREEN_WIDTH
    om, _p1, _p2 = _options()
    keybind_store.save_set("demo", Keymap(dict(_P1)))
    om.keybind_mode = True
    om.sets_mode = True
    surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    for setup in (lambda: om.sets.open(0),                         # menu view
                  lambda: om.sets._begin_list("load"),             # list view
                  lambda: om.sets._begin_text("save"),             # text-entry view
                  lambda: setattr(om.sets, "view", "confirm")):    # confirm view
        om.sets.open(0)
        setup()
        om.render(surf)                                            # must not raise
    assert surf.get_at((5, 5))[:3] == MAIN_MENU_BG_COLOR
