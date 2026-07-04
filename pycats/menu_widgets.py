"""Reusable menu-button widget (#359).

A coloured rectangle that **glows when focused**, plus a redundant, non-colour
focus cue (a leading ► marker), so menu focus is never conveyed by colour alone
(closes an #346 a11y finding; mirrors Project M's cursor+highlight approach, #353).

Piloted in ``OptionsMenu.render``; rolled out to the other menus in #360. Pure
``focus_label`` keeps the marker logic unit-testable; ``draw_menu_button`` owns
the pixels. Headless-safe (plain pygame Surface ops; no display hooks needed).
"""
import pygame

from . import runtime_settings
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
BUTTON_FILL_PRESSED = (120, 120, 40)        # brighter flash on press (#332), decays to the glow
BUTTON_BORDER_FOCUSED = MAIN_MENU_SELECTED_COLOR  # bright border = the "glow" edge
BUTTON_BORDER_UNFOCUSED = (70, 70, 80)      # dim outline when not focused

# How many frames the press-flash lingers after a confirm/navigation input (#332).
# Screens own a ``press_pulse`` counter set to this on input and decremented each
# frame; the button renders ``pressed`` while it is > 0.
PRESS_PULSE_FRAMES = 6


def focus_label(label, focused):
    """The displayed label with a redundant, non-colour focus marker when focused."""
    return f"{FOCUS_MARKER} {label}" if focused else label


def _scaled_chrome():
    """(pad_x, pad_y, radius) scaled by the live font_scale (#402) so the button
    chrome stays proportional to the (already-scaled) label. Identity at standard."""
    s = runtime_settings.font_scale()
    return round(BUTTON_PAD_X * s), round(BUTTON_PAD_Y * s), max(1, round(BUTTON_RADIUS * s))


def menu_button_size(label, size, focused=False, *, min_width=BUTTON_MIN_WIDTH):
    """The (w, h) the button for ``label`` occupies at the live font scale.

    ``min_width`` is a literal pixel floor (callers pass a uniform width so a grid's
    columns line up); the label font itself is scaled inside ``_get_font``."""
    pad_x, pad_y, _ = _scaled_chrome()
    tw, th = text_renderer._get_font(None, size).size(focus_label(label, focused))
    return max(min_width, tw + 2 * pad_x), th + 2 * pad_y


def draw_menu_button(surface, label, center, size, focused, *, min_width=BUTTON_MIN_WIDTH,
                     pressed=False):
    """Draw one menu row as a coloured rect that glows when focused, with a marker.

    ``center`` is the (x, y) the button is centred on; ``size`` the label font size.
    ``pressed`` flashes the focused row a brighter fill (``BUTTON_FILL_PRESSED``) for
    press feedback (#332); it is a no-op when unfocused. Returns the button
    ``pygame.Rect``. Visual only — no navigation/state logic. Chrome (padding/radius)
    scales with the live font_scale (#402); at the standard scale, with the default
    ``pressed=False``, the render is byte-identical to before.
    """
    _, _, radius = _scaled_chrome()
    text = focus_label(label, focused)
    w, h = menu_button_size(label, size, focused=focused, min_width=min_width)
    rect = pygame.Rect(0, 0, w, h)
    rect.center = center

    if focused:
        fill = BUTTON_FILL_PRESSED if pressed else BUTTON_FILL_FOCUSED
        pygame.draw.rect(surface, fill, rect, border_radius=radius)
        pygame.draw.rect(surface, BUTTON_BORDER_FOCUSED, rect, width=3, border_radius=radius)
        color = MAIN_MENU_SELECTED_COLOR
    else:
        pygame.draw.rect(surface, BUTTON_BORDER_UNFOCUSED, rect, width=1, border_radius=radius)
        color = MAIN_MENU_OPTION_COLOR

    # Center the label in the rect on BOTH axes (#389) — render_text_mixed only
    # centers horizontally (text top sits at y), which left labels low in the box.
    text_renderer.render_mixed_centered(text, size, color, surface, center)
    return rect
