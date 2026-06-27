"""Headless integration test for hold-ESC-to-quit (#113).

Simulates holding ESC for 120+ frames and verifies should_quit fires.
"""
import os
import tempfile

_TMP_CONFIG = tempfile.mkdtemp(prefix="pycats_test_")
os.environ["PYCATS_CONFIG_DIR"] = _TMP_CONFIG
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
pygame.init()

from pycats.core import input as _input


def InputFrame(held=None, pressed=None, released=None):
    return _input.InputFrame(
        held=held or set(),
        pressed=pressed or set(),
        released=released or set(),
    )
from pycats.screen_manager import ScreenStateManager


def make_sm(state="main_menu"):
    """Create a minimal ScreenStateManager with just the esc-quit attributes."""
    sm = ScreenStateManager.__new__(ScreenStateManager)
    sm.should_quit = False
    sm.esc_quit_to_menu = False
    sm.esc_quit_timer = 0
    sm.esc_quit_hold_frames = 120
    sm.fsm = type('FSM', (), {'state': state})()
    return sm


def test_esc_hold_fires_quit():
    sm = make_sm()
    for _ in range(119):
        fi = InputFrame(held={pygame.K_ESCAPE}, pressed=set())
        sm._tick_esc_quit_timer(fi)
    assert sm.should_quit is False, "Should NOT quit at 119 frames"

    fi = InputFrame(held={pygame.K_ESCAPE}, pressed=set())
    sm._tick_esc_quit_timer(fi)
    assert sm.should_quit is True, "SHOULD quit at 120 frames"
    print("PASS: ESC hold fires quit at 120 frames")


def test_esc_release_resets_timer():
    sm = make_sm()
    for _ in range(50):
        fi = InputFrame(held={pygame.K_ESCAPE}, pressed=set())
        sm._tick_esc_quit_timer(fi)
    assert sm.esc_quit_timer == 50

    # Release ESC
    fi = InputFrame(held=set(), pressed=set())
    sm._tick_esc_quit_timer(fi)
    assert sm.esc_quit_timer == 0, "Timer should reset on release"
    assert sm.should_quit is False
    print("PASS: ESC release resets timer")


def test_toggle_off_prevents_quit():
    import pycats.settings as settings_mod
    orig_load = settings_mod.load
    settings_mod.load = lambda: {"esc_hold_to_quit": False}

    sm = make_sm()
    for _ in range(200):
        fi = InputFrame(held={pygame.K_ESCAPE}, pressed=set())
        sm._tick_esc_quit_timer(fi)
    assert sm.should_quit is False, "Should NOT quit when setting is False"
    assert sm.esc_quit_timer == 0, "Timer should stay at 0 when disabled"
    settings_mod.load = orig_load
    print("PASS: toggle off prevents quit")


def test_no_esc_hold_does_nothing():
    sm = make_sm()
    for _ in range(200):
        fi = InputFrame(held={pygame.K_a}, pressed=set())
        sm._tick_esc_quit_timer(fi)
    assert sm.should_quit is False
    assert sm.esc_quit_timer == 0
    print("PASS: no ESC hold does nothing")


def test_esc_hold_in_playing_state_quits_to_menu():
    sm = make_sm(state="playing")
    for _ in range(120):
        fi = InputFrame(held={pygame.K_ESCAPE}, pressed=set())
        sm._tick_esc_quit_timer(fi)
    assert sm.should_quit is False, "should_quit should stay False in playing state"
    assert sm.esc_quit_to_menu is True, "esc_quit_to_menu should be True (return to menu, not exit)"
    print("PASS: ESC hold in playing state signals quit-to-menu")


def test_esc_hold_in_main_menu_exits_app():
    sm = make_sm(state="main_menu")
    for _ in range(120):
        fi = InputFrame(held={pygame.K_ESCAPE}, pressed=set())
        sm._tick_esc_quit_timer(fi)
    assert sm.should_quit is True, "should_quit should be True"
    assert sm.esc_quit_to_menu is False, "esc_quit_to_menu should be False (exit app)"
    print("PASS: ESC hold in main_menu signals exit app")


if __name__ == "__main__":
    test_esc_hold_fires_quit()
    test_esc_release_resets_timer()
    test_toggle_off_prevents_quit()
    test_no_esc_hold_does_nothing()
    test_esc_hold_in_playing_state_quits_to_menu()
    test_esc_hold_in_main_menu_exits_app()
    print("\nAll integration tests passed!")
