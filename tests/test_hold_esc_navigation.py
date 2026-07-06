"""Unified hold-Esc navigation (#453).

A 2-second hold of ESC pops exactly one level up the screen ladder; holding at
main_menu quits the app. Drives the REAL ScreenStateManager through its public
``update()`` / ``get_state()`` interface (no internal timer pokes), so the tests
read as the behavior spec and survive an internals refactor.

Ladder (2s hold):
  playing / pause / win_screen -> char_select
  char_select / options        -> main_menu
  main_menu                    -> quit app
"""


import pygame
import pytest

from pycats.core.input import InputFrame
from pycats.screen_manager import ScreenStateManager

_P1 = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w, down=pygame.K_s,
           attack=pygame.K_v, special=pygame.K_c, shield=pygame.K_x)
_P2 = dict(left=pygame.K_LEFT, right=pygame.K_RIGHT, up=pygame.K_UP, down=pygame.K_DOWN,
           attack=pygame.K_PERIOD, special=pygame.K_SLASH, shield=pygame.K_RSHIFT)

HOLD = 120  # esc_quit_hold_frames (2s @ 60 FPS)


@pytest.fixture(autouse=True)
def _isolated_config(tmp_path, monkeypatch):
    """Each test writes/reads settings under its own config dir (default = on)."""
    monkeypatch.setenv("PYCATS_CONFIG_DIR", str(tmp_path))
    pygame.init()


def _esc():
    return InputFrame(held={pygame.K_ESCAPE}, pressed=set(), released=set())


def _empty():
    return InputFrame(held=set(), pressed=set(), released=set())


def _mk(state="main_menu"):
    sm = ScreenStateManager(_P1, _P2)
    if state != "main_menu":
        sm.engine.force(state)
    return sm


def _hold_esc(sm, frames, battle=None):
    for _ in range(frames):
        sm.update(_esc(), battle)


def test_options_hold_esc_backs_out_to_main_menu():
    sm = _mk("options")
    _hold_esc(sm, HOLD)
    assert sm.get_state() == "main_menu"


def test_char_select_hold_esc_backs_out_to_main_menu():
    sm = _mk("char_select")
    _hold_esc(sm, HOLD)
    assert sm.get_state() == "main_menu"


def test_playing_hold_esc_drops_to_char_select():
    sm = _mk("playing")
    _hold_esc(sm, HOLD)
    assert sm.get_state() == "char_select"


def test_pause_hold_esc_drops_to_char_select():
    sm = _mk("pause")
    _hold_esc(sm, HOLD)
    assert sm.get_state() == "char_select"


def test_win_screen_hold_esc_bypasses_confirm_to_char_select():
    sm = _mk()
    # A real win leaves winner/loser set; the both-confirm gate normally holds you
    # on the stats screen. Hold-ESC bypasses it and clears the match (#453, #3).
    sm.set_winner(object(), object())
    sm.engine.force("win_screen")
    _hold_esc(sm, HOLD)
    assert sm.get_state() == "char_select"
    assert sm.winner is None and sm.loser is None


def test_main_menu_hold_esc_quits_app():
    sm = _mk("main_menu")
    _hold_esc(sm, HOLD)
    assert sm.get_state() == "main_menu"
    assert sm.should_quit_game() is True


def test_hold_below_threshold_does_not_pop():
    sm = _mk("options")
    _hold_esc(sm, HOLD - 1)
    assert sm.get_state() == "options"


def test_release_before_threshold_resets_the_hold():
    sm = _mk("options")
    _hold_esc(sm, HOLD - 1)
    sm.update(_empty())          # release
    _hold_esc(sm, HOLD - 1)      # not enough on its own
    assert sm.get_state() == "options"


def test_setting_off_makes_esc_inert(monkeypatch):
    import pycats.settings as settings_mod
    monkeypatch.setattr(settings_mod, "load",
                        lambda: {"esc_hold_to_navigate": False})
    sm = _mk("options")
    _hold_esc(sm, HOLD * 2)
    assert sm.get_state() == "options"
    assert sm.should_quit_game() is False


def test_popping_one_level_does_not_cascade_to_a_second():
    """Holding ESC past a pop (options->main_menu) must not immediately quit the
    app on the same continuous hold — the timer resets on entering main_menu."""
    sm = _mk("options")
    _hold_esc(sm, HOLD + 5)      # keep holding a few frames past the pop
    assert sm.get_state() == "main_menu"
    assert sm.should_quit_game() is False


def test_pause_menu_return_to_char_select_action():
    sm = _mk("pause")
    sm.pause_menu.action_requested = "return_to_char_select"
    sm.update(_empty())
    assert sm.get_state() == "char_select"
