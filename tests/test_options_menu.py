"""Main-menu Options sub-menu (#121).

The Options screen flips HUD/display settings: the status-bars toggle persists
through settings.py + updates the live runtime accessor; the display rows call
back into game.py through injected hooks (faked here). Navigation wraps; B backs
out; the FSM gains an `options` state reachable from and returning to the menu.
"""
import contextlib

import pygame

from pycats import runtime_settings, settings
from pycats.config import MAIN_MENU_OPTION_SIZE, SCREEN_HEIGHT, SCREEN_WIDTH
from pycats.core.input import InputFrame
from pycats.menu_widgets import menu_button_size
from pycats.options_menu import ROW_DESCRIPTIONS, OptionsMenu
from pycats.screen_manager import ScreenStateManager

P1 = {"up": pygame.K_w, "down": pygame.K_s, "left": pygame.K_a, "right": pygame.K_d,
      "attack": pygame.K_v, "special": pygame.K_c}
P2 = {"up": pygame.K_UP, "down": pygame.K_DOWN, "left": pygame.K_LEFT,
      "right": pygame.K_RIGHT, "attack": pygame.K_SLASH, "special": pygame.K_PERIOD}

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


def test_esc_quit_row_toggles_setting_and_persists(tmp_path, monkeypatch):
    monkeypatch.setenv("PYCATS_CONFIG_DIR", str(tmp_path))
    settings.save({"esc_hold_to_navigate": True})
    m = _opts()
    m.selected_option = m.rows.index("esc_quit")
    m.update({ATTACK})
    assert settings.load()["esc_hold_to_navigate"] is False

    m.input_cooldown = 0
    m.update({ATTACK})
    assert settings.load()["esc_hold_to_navigate"] is True


def test_esc_quit_row_label_reflects_persisted_setting(tmp_path, monkeypatch):
    monkeypatch.setenv("PYCATS_CONFIG_DIR", str(tmp_path))
    m = _opts()

    settings.save({"esc_hold_to_navigate": True})
    assert m._row_label("esc_quit") == "Hold-ESC Back: ON"

    settings.save({"esc_hold_to_navigate": False})
    assert m._row_label("esc_quit") == "Hold-ESC Back: OFF"


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


def test_nav_down_wraps_within_column():
    # 2-column grid (#389): down steps a full row within the column and wraps.
    # Derived from the live row count so adding a row (e.g. #345 font_scale) is fine.
    from pycats.options_menu import NCOLS
    m = _opts()
    nrows = (len(m.rows) + NCOLS - 1) // NCOLS
    expected = [(r % nrows) * NCOLS for r in range(1, nrows + 1)]
    assert m.selected_option == 0
    for want in expected:
        m.input_cooldown = 0
        m.update({pygame.K_s})  # down
        assert m.selected_option == want


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


# --- #390: focused-option captions (content + visibility/no-overlap) ---
@contextlib.contextmanager
def _scale(preset):
    prev = runtime_settings.get("font_scale")
    runtime_settings.set("font_scale", preset)
    try:
        yield
    finally:
        runtime_settings.set("font_scale", prev)


def test_focused_row_caption():
    """Every row maps to its frozen description, and the focused caption tracks the
    selection. Able-to-fail: no ROW_DESCRIPTIONS / _focused_caption before the feature."""
    runtime_settings.seed(settings.defaults())
    m = _opts()
    for i, row in enumerate(m.rows):
        m.selected_option = i
        assert m._focused_caption() == ROW_DESCRIPTIONS[row]
    m.selected_option = 0
    first = m._focused_caption()
    m.selected_option = 1
    assert m._focused_caption() != first  # updates live as focus moves


def test_caption_never_overlaps_buttons():
    """#390 added acceptance: for EVERY option, when focused, the caption is fully on
    screen and overlaps no button — at both standard and large font_scale."""
    runtime_settings.seed(settings.defaults())
    m = _opts()
    for preset in ("standard", "large"):
        with _scale(preset):
            for sel in range(len(m.rows)):
                m.selected_option = sel
                m.scroll_top = 0
                placements, meta = m._layout()
                bw = meta["button_width"]
                _, bh = menu_button_size(m._row_label(m.rows[0]), MAIN_MENU_OPTION_SIZE,
                                         focused=True, min_width=bw)
                button_rects = []
                for _i, (cx, cy) in placements:
                    r = pygame.Rect(0, 0, bw, bh)
                    r.center = (cx, cy)
                    button_rects.append(r)
                _cap_text, cap_rect = m._caption_layout(meta)
                assert cap_rect.width <= SCREEN_WIDTH, f"caption wider than screen @{preset}"
                assert 0 <= cap_rect.left and cap_rect.right <= SCREEN_WIDTH, \
                    f"caption off-screen horizontally @{preset} sel={sel}: {cap_rect}"
                assert 0 <= cap_rect.top and cap_rect.bottom <= SCREEN_HEIGHT, \
                    f"caption off-screen vertically @{preset} sel={sel}: {cap_rect}"
                for br in button_rects:
                    assert not cap_rect.colliderect(br), \
                        f"caption overlaps a button @{preset} sel={sel}: {cap_rect} vs {br}"
