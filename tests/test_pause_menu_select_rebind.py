"""Pause menu select honors an attack rebind (#842, verified in #836).

`PauseMenuManager.update` used to decide "select" against hardcoded
`pygame.K_SLASH` / `pygame.K_v`, while `MainMenuManager` reads the rebindable
`p1/p2_controls["attack"]`. Both managers are handed the same live keymap, so a
player who rebinds attack away from the defaults (`v` for P1, `/` for P2) found
the pause menu's select deaf to their rebound key — navigation honored the
rebind, but select did not. These tests pin: (a) a rebound attack key selects,
and (b) the default attack key still selects (no regression for the common case).
"""

import pygame

from pycats.pause_menu import PauseMenuManager

# Defaults match app.P1_KEYS / P2_KEYS (attack = K_v / K_SLASH).
DEFAULT_P1 = {"up": pygame.K_w, "down": pygame.K_s, "attack": pygame.K_v}
DEFAULT_P2 = {"up": pygame.K_UP, "down": pygame.K_DOWN, "attack": pygame.K_SLASH}


def test_rebound_p1_attack_key_selects():
    # P1 rebinds attack v -> j; the pause menu must select on j.
    p1 = {"up": pygame.K_w, "down": pygame.K_s, "attack": pygame.K_j}
    m = PauseMenuManager(p1, DEFAULT_P2)
    m.selected_option = 0  # Resume
    m.update({pygame.K_j})
    assert m.get_action() == "resume"


def test_rebound_p2_attack_key_selects():
    # P2 rebinds attack / -> k; the pause menu must select on k.
    p2 = {"up": pygame.K_UP, "down": pygame.K_DOWN, "attack": pygame.K_k}
    m = PauseMenuManager(DEFAULT_P1, p2)
    m.selected_option = 1  # End Match
    m.update({pygame.K_k})
    assert m.get_action() == "end_match"


def test_default_attack_keys_still_select():
    # No regression for the common (default-bound) case.
    m = PauseMenuManager(DEFAULT_P1, DEFAULT_P2)
    m.selected_option = 2  # Return to Character Select
    m.update({pygame.K_v})
    assert m.get_action() == "return_to_char_select"

    m = PauseMenuManager(DEFAULT_P1, DEFAULT_P2)
    m.selected_option = 0
    m.update({pygame.K_SLASH})
    assert m.get_action() == "resume"
