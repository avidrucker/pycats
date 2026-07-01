"""Main-menu Options sub-menu (#121).

A consolidated settings screen reachable from the main menu — pycats's deliberate,
ratified divergence from Project M's distributed settings model (#122; global/HUD
prefs here, per-player config stays on char-select). Each change persists through
`settings.py` and updates the live value so it takes effect immediately:

- **Status Bars** (HUD overlay #111): flips `runtime_settings` live + persists.
- **Hitbox Overlay** (debug box visualiser #219): flips `runtime_settings` live
  + persists; the battle render path draws hit/hurtbox outlines when ON.
- **Window Size / Fullscreen** (display): routed back to game.py via injected
  `display_hooks` (None in headless/tests → those rows are inert). The hooks reuse
  game.py's existing F10/F11 machinery, which already persists display prefs.
- **Hold-ESC Quit**: flips the persisted hold-ESC-to-quit setting (#113).

Nav convention (research #115 §10.4): up/down move, A (attack) confirms/toggles,
B (special) backs out.
"""
import pygame  # type: ignore
from .config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    WHITE,
    MAIN_MENU_BG_COLOR,
    MAIN_MENU_TITLE_COLOR,
    MAIN_MENU_TITLE_SIZE,
    MAIN_MENU_OPTION_SIZE,
    MAIN_MENU_PADDING,
    MAIN_MENU_OPTION_SPACING,
    FONT_SCALE_ORDER,
    FONT_SCALE_NAMES,
)
from . import runtime_settings
from . import settings
from .menu_widgets import draw_menu_button
from .text_utils import text_renderer

# The rows lay out as a 2-column grid (#389) — row-major, so index i is at
# (row=i//NCOLS, col=i%NCOLS). Navigation is 2D: up/down move a full row within a
# column, left/right move between columns.
NCOLS = 2


class OptionsMenu:
    """Consolidated Options screen: navigation, toggles, and rendering."""

    def __init__(self, p1_controls, p2_controls, display_hooks=None):
        self.p1_controls = p1_controls
        self.p2_controls = p2_controls
        # Optional callables wiring display settings to game.py (None in
        # headless/tests → display rows render but do nothing on activate).
        self.display_hooks = display_hooks or {}

        # Row keys in display order. "back" is the explicit exit row.
        self.rows = ["status_bars", "hitbox_overlay", "input_history", "controls",
                     "font_scale", "window_scale", "fullscreen", "esc_quit", "back"]
        self.selected_option = 0

        self.input_cooldown = 0
        self.action_requested = None  # "back" or None

    def reset(self):
        self.selected_option = 0
        self.input_cooldown = 0
        self.action_requested = None

    # ---- input ----
    def _pressed(self, action, pressed_keys):
        """True if either player's ``action`` key is down this frame. Uses .get so a
        partial control dict (e.g. no left/right bound) is inert, not a KeyError."""
        a = self.p1_controls.get(action)
        b = self.p2_controls.get(action)
        return (a is not None and a in pressed_keys) or (
            b is not None and b in pressed_keys
        )

    def update(self, pressed_keys):
        if self.input_cooldown > 0:
            self.input_cooldown -= 1
            return

        # B / special backs out from any row.
        if self._pressed("special", pressed_keys):
            self.action_requested = "back"
            self.input_cooldown = 20
            return

        # 2D grid navigation (#389): up/down move a full row within a column,
        # left/right move between columns. Both wrap.
        n = len(self.rows)
        nrows = (n + NCOLS - 1) // NCOLS
        row, col = divmod(self.selected_option, NCOLS)
        moved = False
        if self._pressed("up", pressed_keys):
            row = (row - 1) % nrows
            moved = True
        if self._pressed("down", pressed_keys):
            row = (row + 1) % nrows
            moved = True
        if self._pressed("left", pressed_keys):
            col = (col - 1) % NCOLS
            moved = True
        if self._pressed("right", pressed_keys):
            col = (col + 1) % NCOLS
            moved = True
        if moved:
            new = row * NCOLS + col
            if new >= n:  # partial last row (odd count) — snap to the last cell
                new = n - 1
            self.selected_option = new
            self.input_cooldown = 10

        if self._pressed("attack", pressed_keys):
            self._activate(self.rows[self.selected_option])
            self.input_cooldown = 20

    def _activate(self, row):
        if row == "status_bars":
            new = not runtime_settings.show_status_timer_bars()
            runtime_settings.set("show_status_timer_bars", new)
            settings.save({"show_status_timer_bars": new})
        elif row == "hitbox_overlay":
            new = not runtime_settings.show_hitbox_overlay()
            runtime_settings.set("show_hitbox_overlay", new)
            settings.save({"show_hitbox_overlay": new})
        elif row == "input_history":
            new = not runtime_settings.show_input_history()
            runtime_settings.set("show_input_history", new)
            settings.save({"show_input_history": new})
        elif row == "controls":
            new = not runtime_settings.show_controls()
            runtime_settings.set("show_controls", new)
            settings.save({"show_controls": new})
        elif row == "font_scale":
            # Cycle Small -> Standard -> Large (#345); live + persisted.
            cur = runtime_settings.get("font_scale")
            order = FONT_SCALE_ORDER
            idx = order.index(cur) if cur in order else order.index("standard")
            new = order[(idx + 1) % len(order)]
            runtime_settings.set("font_scale", new)
            settings.save({"font_scale": new})
        elif row == "window_scale":
            hook = self.display_hooks.get("cycle_windowed_scale")
            if hook:
                hook()
        elif row == "fullscreen":
            hook = self.display_hooks.get("toggle_fullscreen")
            if hook:
                hook()
        elif row == "esc_quit":
            prefs = settings.load()
            settings.save(
                {"esc_hold_to_quit": not prefs.get("esc_hold_to_quit", True)}
            )
        elif row == "back":
            self.action_requested = "back"

    # ---- labels ----
    def _row_label(self, row):
        if row == "status_bars":
            return "Status Bars: " + ("ON" if runtime_settings.show_status_timer_bars() else "OFF")
        if row == "hitbox_overlay":
            return "Hitbox Overlay: " + ("ON" if runtime_settings.show_hitbox_overlay() else "OFF")
        if row == "input_history":
            return "Input History: " + ("ON" if runtime_settings.show_input_history() else "OFF")
        if row == "controls":
            return "Controls: " + ("ON" if runtime_settings.show_controls() else "OFF")
        if row == "font_scale":
            return "Font Size: " + FONT_SCALE_NAMES.get(
                runtime_settings.get("font_scale"), "Standard")
        if row == "window_scale":
            getter = self.display_hooks.get("get_windowed_scale")
            return "Window Size: " + (f"{getter():g}x" if getter else "F10")
        if row == "fullscreen":
            getter = self.display_hooks.get("is_fullscreen")
            return "Fullscreen: " + (("ON" if getter() else "OFF") if getter else "F11")
        if row == "esc_quit":
            return "Hold-ESC Quit: " + (
                "ON" if settings.load().get("esc_hold_to_quit", True) else "OFF"
            )
        if row == "back":
            return "Back"
        return row

    # ---- render ----
    def render(self, surface):
        surface.fill(MAIN_MENU_BG_COLOR)
        text_renderer.render_text_simple(
            "Options",
            MAIN_MENU_TITLE_SIZE,
            MAIN_MENU_TITLE_COLOR,
            surface,
            (SCREEN_WIDTH // 2, MAIN_MENU_PADDING + MAIN_MENU_TITLE_SIZE // 2),
            center=True,
        )

        start_y = MAIN_MENU_PADDING + MAIN_MENU_TITLE_SIZE + MAIN_MENU_PADDING
        # 2-column grid (#389): row-major, one column centred either side of centre.
        # Two columns halve the vertical extent so the rows no longer overflow into
        # the instruction line below (#386 follow-up).
        col_x = (SCREEN_WIDTH // 4, SCREEN_WIDTH * 3 // 4)
        for i, row in enumerate(self.rows):
            r, c = divmod(i, NCOLS)
            center = (col_x[c], start_y + r * MAIN_MENU_OPTION_SPACING)
            # Each row is a menu-button widget (#359): a coloured rect that glows
            # when focused, with a redundant ► marker (focus not colour-only, #346).
            draw_menu_button(
                surface,
                self._row_label(row),
                center,
                MAIN_MENU_OPTION_SIZE,
                focused=(i == self.selected_option),
            )

        instructions = ["Use WASD or arrows to navigate", "A to toggle, B to go back"]
        instruction_start_y = SCREEN_HEIGHT - len(instructions) * 30 - MAIN_MENU_PADDING
        for i, instruction in enumerate(instructions):
            text_renderer.render_text_mixed(
                instruction,
                20,
                WHITE,
                surface,
                (SCREEN_WIDTH // 2, instruction_start_y + i * 30),
                center=True,
            )
