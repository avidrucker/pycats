"""Reusable menu-button widget (#359).

A coloured rectangle that **glows when focused**, plus a redundant, non-colour
focus cue (a leading ► marker), so menu focus is never conveyed by colour alone
(closes an #346 a11y finding; mirrors Project M's cursor+highlight approach, #353).

Piloted in ``OptionsMenu.render``; rolled out to the other menus in #360. Pure
``focus_label`` keeps the marker logic unit-testable; ``draw_menu_button`` owns
the pixels. Headless-safe (plain pygame Surface ops; no display hooks needed).
"""
import pygame

from .config import MAIN_MENU_OPTION_COLOR, MAIN_MENU_SELECTED_COLOR
from .text_utils import text_renderer

# ► (U+25BA) is in text_utils' font-capability probe, so it always renders.
FOCUS_MARKER = "►"

# Button chrome
BUTTON_PAD_X = 24            # horizontal padding around the label
BUTTON_PAD_Y = 8            # vertical padding
BUTTON_MIN_WIDTH = 300       # keep rows a consistent width regardless of label
BUTTON_RADIUS = 6
BUTTON_FILL_FOCUSED = (60, 60, 20)          # warm glow fill behind the focused label
BUTTON_BORDER_FOCUSED = MAIN_MENU_SELECTED_COLOR  # bright border = the "glow" edge
BUTTON_BORDER_UNFOCUSED = (70, 70, 80)      # dim outline when not focused


def focus_label(label, focused):
    """The displayed label with a redundant, non-colour focus marker when focused."""
    return f"{FOCUS_MARKER} {label}" if focused else label


def draw_menu_button(surface, label, center, size, focused, *, min_width=BUTTON_MIN_WIDTH):
    """Draw one menu row as a coloured rect that glows when focused, with a marker.

    ``center`` is the (x, y) the button is centred on; ``size`` the label font size.
    Returns the button ``pygame.Rect``. Visual only — no navigation/state logic.
    """
    text = focus_label(label, focused)
    tw, th = text_renderer._get_font(None, size).size(text)
    rect = pygame.Rect(0, 0, max(min_width, tw + 2 * BUTTON_PAD_X), th + 2 * BUTTON_PAD_Y)
    rect.center = center

    if focused:
        pygame.draw.rect(surface, BUTTON_FILL_FOCUSED, rect, border_radius=BUTTON_RADIUS)
        pygame.draw.rect(surface, BUTTON_BORDER_FOCUSED, rect, width=3, border_radius=BUTTON_RADIUS)
        color = MAIN_MENU_SELECTED_COLOR
    else:
        pygame.draw.rect(surface, BUTTON_BORDER_UNFOCUSED, rect, width=1, border_radius=BUTTON_RADIUS)
        color = MAIN_MENU_OPTION_COLOR

    text_renderer.render_text_mixed(text, size, color, surface, center, center=True)
    return rect
