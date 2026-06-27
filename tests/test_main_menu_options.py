"""Main menu gains an Options entry and N-option navigation (#121).

The menu was hardcoded to two options (Play/Quit) with a `1 - selected` flip;
adding Options makes it three, so navigation must wrap over N and selecting
Options must request the `options` action the screen FSM transitions on.
"""
import pygame

from pycats.main_menu import MainMenuManager

P1 = {"up": pygame.K_w, "down": pygame.K_s, "attack": pygame.K_v}
P2 = {"up": pygame.K_UP, "down": pygame.K_DOWN, "attack": pygame.K_SLASH}


def _menu():
    return MainMenuManager(P1, P2)


def test_options_entry_sits_between_play_and_quit():
    m = _menu()
    assert m.options == ["Play", "Options", "Quit"]


def test_selecting_options_requests_options_action():
    m = _menu()
    m.selected_option = m.options.index("Options")
    m.update({pygame.K_v})
    assert m.action_requested == "options"


def test_selecting_play_and_quit_still_work():
    m = _menu()
    m.selected_option = m.options.index("Play")
    m.update({pygame.K_v})
    assert m.action_requested == "play"

    m = _menu()
    m.selected_option = m.options.index("Quit")
    m.update({pygame.K_v})
    assert m.action_requested == "quit"


def test_down_navigation_wraps_over_three_options():
    m = _menu()
    assert m.selected_option == 0
    for expected in (1, 2, 0):  # Play -> Options -> Quit -> wrap to Play
        m.input_cooldown = 0
        m.update({pygame.K_s})
        assert m.selected_option == expected


def test_up_navigation_wraps_backwards():
    m = _menu()
    assert m.selected_option == 0
    m.input_cooldown = 0
    m.update({pygame.K_w})  # up from Play wraps to Quit
    assert m.selected_option == 2
