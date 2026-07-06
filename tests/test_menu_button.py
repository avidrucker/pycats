"""Reusable menu-button widget (#359) — glow-on-focus + redundant marker.

A coloured rect that brightens/glows when focused, plus a non-colour focus cue
(a leading ► marker), so menu focus isn't conveyed by colour alone (#346). Pure
`focus_label` is unit-tested for the marker; `draw_menu_button` for the glow.
Piloted in OptionsMenu here; rolled out to the other menus in #360.
"""


import pygame  # noqa: E402

from pycats.menu_widgets import (  # noqa: E402
    BUTTON_FILL_FOCUSED,
    FOCUS_MARKER,
    draw_menu_button,
    focus_label,
)


def _surf(w=400, h=80):
    pygame.font.init()
    s = pygame.Surface((w, h))
    s.fill((0, 0, 0))
    return s


def _bytes(s):
    return pygame.image.tobytes(s, "RGB")


def _row_has_fill(surface, y, color, x0=60, x1=340):
    return any(surface.get_at((x, y))[:3] == color for x in range(x0, x1))


# ---- focus_label: redundant, non-colour marker ---------------------------- #
def test_focus_label_adds_marker_when_focused():
    assert focus_label("Play", True) == f"{FOCUS_MARKER} Play"


def test_focus_label_plain_when_unfocused():
    assert focus_label("Play", False) == "Play"


# ---- draw_menu_button: glow rect ------------------------------------------ #
def test_focused_button_differs_from_unfocused():
    a, b = _surf(), _surf()
    draw_menu_button(a, "Play", (200, 40), 36, focused=True)
    draw_menu_button(b, "Play", (200, 40), 36, focused=False)
    assert _bytes(a) != _bytes(b)


def test_focused_button_draws_glow_fill():
    s = _surf()
    draw_menu_button(s, "Play", (200, 40), 36, focused=True)
    assert _row_has_fill(s, 40, BUTTON_FILL_FOCUSED)  # glow fill present on the row


def test_unfocused_button_has_no_glow_fill():
    s = _surf()
    draw_menu_button(s, "Play", (200, 40), 36, focused=False)
    assert not _row_has_fill(s, 40, BUTTON_FILL_FOCUSED)  # no glow when unfocused


def test_returns_rect_centered_at_position():
    s = _surf()
    rect = draw_menu_button(s, "Play", (200, 40), 36, focused=True)
    assert isinstance(rect, pygame.Rect)
    assert rect.center == (200, 40)


# ---- pilot integration: OptionsMenu.render uses the widget ----------------- #
from pycats import runtime_settings, settings  # noqa: E402
from pycats.config import (  # noqa: E402
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from pycats.options_menu import OptionsMenu  # noqa: E402

_P1 = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w, down=pygame.K_s,
           attack=pygame.K_v, special=pygame.K_c, shield=pygame.K_x)
_P2 = dict(left=pygame.K_LEFT, right=pygame.K_RIGHT, up=pygame.K_UP, down=pygame.K_DOWN,
           attack=pygame.K_PERIOD, special=pygame.K_SLASH, shield=pygame.K_RSHIFT)


def test_options_render_draws_glow_button_only_at_focused_row():
    # Layout-agnostic (#402 made positions scale-dependent): ask the menu where it
    # drew each button, then assert the glow fill is under the focused one only.
    runtime_settings.seed(settings.defaults())
    m = OptionsMenu(_P1, _P2)  # selected_option defaults to 0
    s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    m.render(s)
    centers = {i: c for i, c in m._layout()[0]}
    fx, fy = centers[0]   # focused cell
    ux, uy = centers[3]   # a different, unfocused cell
    assert _row_has_fill(s, fy, BUTTON_FILL_FOCUSED, fx - 150, fx + 150)      # focused
    assert not _row_has_fill(s, uy, BUTTON_FILL_FOCUSED, ux - 150, ux + 150)  # unfocused
