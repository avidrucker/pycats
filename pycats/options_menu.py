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
    MAIN_MENU_OPTION_COLOR,
    MAIN_MENU_SELECTED_COLOR,
    MAIN_MENU_PADDING,
    MAIN_MENU_OPTION_SPACING,
)
from . import runtime_settings
from . import settings
from .text_utils import text_renderer


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
                     "window_scale", "fullscreen", "esc_quit", "back"]
        self.selected_option = 0

        self.input_cooldown = 0
        self.action_requested = None  # "back" or None

    def reset(self):
        self.selected_option = 0
        self.input_cooldown = 0
        self.action_requested = None

    # ---- input ----
    def update(self, pressed_keys):
        if self.input_cooldown > 0:
            self.input_cooldown -= 1
            return

        # B / special backs out from any row.
        if (
            self.p1_controls["special"] in pressed_keys
            or self.p2_controls["special"] in pressed_keys
        ):
            self.action_requested = "back"
            self.input_cooldown = 20
            return

        if (
            self.p1_controls["up"] in pressed_keys
            or self.p2_controls["up"] in pressed_keys
        ):
            self.selected_option = (self.selected_option - 1) % len(self.rows)
            self.input_cooldown = 10

        if (
            self.p1_controls["down"] in pressed_keys
            or self.p2_controls["down"] in pressed_keys
        ):
            self.selected_option = (self.selected_option + 1) % len(self.rows)
            self.input_cooldown = 10

        if (
            self.p1_controls["attack"] in pressed_keys
            or self.p2_controls["attack"] in pressed_keys
        ):
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
        for i, row in enumerate(self.rows):
            if i == self.selected_option:
                color = MAIN_MENU_SELECTED_COLOR
            else:
                color = MAIN_MENU_OPTION_COLOR

            option_y = start_y + i * MAIN_MENU_OPTION_SPACING
            text_renderer.render_text_simple(
                self._row_label(row),
                MAIN_MENU_OPTION_SIZE,
                color,
                surface,
                (SCREEN_WIDTH // 2, option_y),
                center=True,
            )

        instructions = ["Use W/S or ↑/↓ to navigate", "A to toggle, B to go back"]
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
