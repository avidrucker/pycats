"""Main-menu Options sub-menu (#121).

The Options screen flips HUD/display settings: the status-bars toggle persists
through settings.py + updates the live runtime accessor; the display rows call
back into game.py through injected hooks (faked here). Navigation wraps; B backs
out; the FSM gains an `options` state reachable from and returning to the menu.
"""
import pygame

from pycats import runtime_settings, settings
from pycats.options_menu import OptionsMenu
from pycats.screen_manager import ScreenStateManager
from pycats.core.input import InputFrame

P1 = {"up": pygame.K_w, "down": pygame.K_s, "attack": pygame.K_v, "special": pygame.K_c}
P2 = {"up": pygame.K_UP, "down": pygame.K_DOWN, "attack": pygame.K_SLASH,
      "special": pygame.K_PERIOD}

ATTACK = pygame.K_v   # "A" / confirm-toggle
BACK = pygame.K_c     # P1 "special" / B / back


def _opts(hooks=None):
    return OptionsMenu(P1, P2, display_hooks=hooks)


def _fake_display_hooks(calls):
    return {
        "get_windowed_scale": lambda: 1.0,
        "cycle_windowed_scale": lambda: calls.append("cycle"),
        "is_fullscreen": lambda: False,
        "toggle_fullscreen": lambda: calls.append("toggle_fs"),
    }


def test_status_bars_row_toggles_runtime_and_persists(tmp_path, monkeypatch):
    monkeypatch.setenv("PYCATS_CONFIG_DIR", str(tmp_path))
    runtime_settings.seed(settings.defaults())  # ON by default
    m = _opts()
    m.selected_option = m.rows.index("status_bars")
    m.update({ATTACK})
    assert runtime_settings.show_status_timer_bars() is False  # live flip
    assert settings.load()["show_status_timer_bars"] is False  # persisted


def test_window_scale_row_calls_injected_hook():
    calls = []
    m = _opts(_fake_display_hooks(calls))
    m.selected_option = m.rows.index("window_scale")
    m.update({ATTACK})
    assert calls == ["cycle"]


def test_fullscreen_row_calls_injected_hook():
    calls = []
    m = _opts(_fake_display_hooks(calls))
    m.selected_option = m.rows.index("fullscreen")
    m.update({ATTACK})
    assert calls == ["toggle_fs"]


def test_esc_quit_row_is_an_inert_slot_until_113():
    m = _opts()
    m.selected_option = m.rows.index("esc_quit")
    m.update({ATTACK})  # must not crash, must not request anything
    assert m.action_requested is None


def test_back_row_requests_back():
    m = _opts()
    m.selected_option = m.rows.index("back")
    m.update({ATTACK})
    assert m.action_requested == "back"


def test_b_key_backs_out_from_any_row():
    m = _opts()
    m.selected_option = 0
    m.update({BACK})
    assert m.action_requested == "back"


def test_nav_wraps_over_rows():
    m = _opts()
    n = len(m.rows)
    assert m.selected_option == 0
    for step in range(1, n + 1):
        m.input_cooldown = 0
        m.update({pygame.K_s})  # down
        assert m.selected_option == step % n


def test_display_rows_inert_without_hooks():
    m = _opts(hooks=None)  # headless: no game.py wiring
    m.selected_option = m.rows.index("window_scale")
    m.update({ATTACK})  # must not crash
    m.selected_option = m.rows.index("fullscreen")
    m.update({ATTACK})  # must not crash


# --- FSM integration ---

def _frame(pressed=None, held=None):
    return InputFrame(
        held=set(held or []), pressed=set(pressed or []), released=set()
    )


def test_menu_options_action_transitions_to_options_state():
    sm = ScreenStateManager(P1, P2)
    assert sm.get_state() == "main_menu"
    sm.main_menu.action_requested = "options"
    sm.update(_frame())
    assert sm.get_state() == "options"


def test_options_back_returns_to_main_menu():
    sm = ScreenStateManager(P1, P2)
    sm.main_menu.action_requested = "options"
    sm.update(_frame())
    assert sm.get_state() == "options"
    sm.options_menu.action_requested = "back"
    sm.update(_frame())
    assert sm.get_state() == "main_menu"
