"""OptionsMenu keybinding sub-mode wiring (#455) — the thin adapter over KeybindMenu.

Drives OptionsMenu.update with synthetic `pressed` sets (the same edge set the game
feeds it) and asserts the KeybindMenu state / bindings change. Headless (no render).
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from pycats.core.keymap import Keymap
from pycats.options_menu import OptionsMenu

_P1 = {"up": 1, "down": 2, "left": 3, "right": 4, "attack": 5, "special": 6, "shield": 7}
_P2 = {"up": 11, "down": 12, "left": 13, "right": 14, "attack": 15, "special": 16, "shield": 17}


def _options():
    p1, p2 = Keymap(dict(_P1)), Keymap(dict(_P2))
    return OptionsMenu(p1, p2), p1, p2


def test_activating_keybindings_row_enters_the_submode():
    om, _p1, _p2 = _options()
    om.selected_option = om.rows.index("keybindings")
    om._activate("keybindings")
    assert om.keybind_mode is True


def test_submode_attack_begins_capture_then_next_key_binds():
    om, p1, _p2 = _options()
    om.keybind_mode = True
    om.keybind.focus(0, "attack")
    om.update({5})            # 'attack' key -> begin capture
    assert om.keybind.capturing
    om.input_cooldown = 0     # clear the nav cooldown for the next frame
    om.update({99})           # a fresh key -> binds
    assert p1["attack"] == 99
    assert not om.keybind.capturing


def test_submode_conflict_is_flagged_and_not_applied():
    om, p1, _p2 = _options()
    om.keybind_mode = True
    om.keybind.focus(0, "attack")
    om.update({5})
    om.input_cooldown = 0
    om.update({7})            # 7 is already P1's 'shield' -> conflict
    assert p1["attack"] == 5  # untouched
    assert "shield" in om.keybind.message


def test_submode_shield_resets_the_focused_player():
    om, p1, _p2 = _options()
    om.keybind_mode = True
    om.keybind.focus(0, "attack")
    om.keybind.begin_capture()
    om.keybind.capture_key(99)   # P1 attack -> 99
    assert p1["attack"] == 99
    om.input_cooldown = 0
    om.update({7})               # 'shield' key -> reset player 0
    assert p1["attack"] == 5     # restored to factory


def test_submode_special_exits_back_to_options():
    om, _p1, _p2 = _options()
    om.keybind_mode = True
    om.update({6})               # 'special' key -> back
    assert om.keybind_mode is False


def test_keybind_view_renders_without_error():
    import pygame
    pygame.init()
    from pycats.config import SCREEN_WIDTH, SCREEN_HEIGHT, MAIN_MENU_BG_COLOR
    p1 = Keymap(dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w, down=pygame.K_s,
                     attack=pygame.K_v, special=pygame.K_c, shield=pygame.K_x, smash=pygame.K_b))
    p2 = Keymap(dict(left=pygame.K_LEFT, right=pygame.K_RIGHT, up=pygame.K_UP, down=pygame.K_DOWN,
                     attack=pygame.K_SLASH, special=pygame.K_PERIOD, shield=pygame.K_COMMA, smash=pygame.K_QUOTE))
    om = OptionsMenu(p1, p2)
    om.keybind_mode = True
    om.keybind.focus(0, "attack")
    om.keybind.begin_capture()
    surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    om.render(surf)                                  # must not raise
    assert surf.get_at((5, 5))[:3] == MAIN_MENU_BG_COLOR   # the view filled the bg
