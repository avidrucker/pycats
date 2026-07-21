"""Menu-button widget rollout to main_menu + pause_menu (#360, rollout of #359).

Each of these two menus is a single-column option list (like the pre-widget
options_menu), so it should render its rows via the shared `draw_menu_button` widget
— giving every menu the same glowing-rect + redundant-► focus feedback instead of
colour-only text. (char_select is a 2D character grid with dual cursors, not an
option list — out of scope here, split to a follow-up.)

Able-to-fail: before adoption the menus render plain text and never call
`draw_menu_button`, so the spy records no calls and these go red.
"""


from unittest.mock import patch  # noqa: E402

import pygame  # noqa: E402

from pycats import runtime_settings, settings  # noqa: E402
from pycats.config import SCREEN_HEIGHT, SCREEN_WIDTH  # noqa: E402
from pycats.main_menu import MainMenuManager  # noqa: E402
from pycats.pause_menu import PauseMenuManager  # noqa: E402

_P1 = dict(up=pygame.K_w, down=pygame.K_s, left=pygame.K_a, right=pygame.K_d,
           attack=pygame.K_v, special=pygame.K_c)
_P2 = dict(up=pygame.K_UP, down=pygame.K_DOWN, left=pygame.K_LEFT, right=pygame.K_RIGHT,
           attack=pygame.K_SLASH, special=pygame.K_PERIOD)


def _spy_button_calls(render_fn):
    """Return the (label, focused) tuples that `render_fn` passes to draw_menu_button.

    Patched at its definition site `pycats.menu_widgets.draw_menu_button`: since #837
    the menus render their rows through the shared `draw_menu_screen` helper (which
    calls `draw_menu_button` in menu_widgets' own namespace) rather than referencing
    the widget directly, so the spy targets the widget module, not the screen module.
    The fake returns a real Rect so callers that use the return value keep working."""
    calls = []

    def fake(surface, label, center, size, focused, **kw):
        calls.append((label, focused))
        return pygame.Rect(0, 0, 1, 1)

    with patch("pycats.menu_widgets.draw_menu_button", side_effect=fake):
        render_fn()
    return calls


def _assert_one_focused_at_selected(calls, options, selected):
    assert calls, "menu must render its rows via draw_menu_button"
    labels = [label for label, _ in calls]
    assert labels == list(options), f"expected one button per option in order, got {labels}"
    focused_idxs = [i for i, (_, f) in enumerate(calls) if f]
    assert focused_idxs == [selected], f"exactly the selected row is focused, got {focused_idxs}"


def test_main_menu_renders_rows_via_widget():
    runtime_settings.seed(settings.defaults())
    m = MainMenuManager(_P1, _P2)
    m.selected_option = 1  # "Options"
    surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    calls = _spy_button_calls(lambda: m.render(surf))
    _assert_one_focused_at_selected(calls, m.options, 1)


def test_pause_menu_renders_rows_via_widget():
    runtime_settings.seed(settings.defaults())
    m = PauseMenuManager(_P1, _P2)
    m.selected_option = 2  # "Return to Character Select"
    surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    calls = _spy_button_calls(lambda: m.render(surf))
    _assert_one_focused_at_selected(calls, m.options, 2)


def test_focus_moves_with_selection_main_menu():
    runtime_settings.seed(settings.defaults())
    m = MainMenuManager(_P1, _P2)
    surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    for sel in range(len(m.options)):
        m.selected_option = sel
        calls = _spy_button_calls(lambda: m.render(surf))
        _assert_one_focused_at_selected(calls, m.options, sel)
