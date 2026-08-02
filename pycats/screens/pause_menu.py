"""
Pause menu screen logic for the cat fighting game.

This module handles:
- Displaying the pause menu with game options
- Menu navigation and selection during pause
- Visual feedback for menu options
- Handling input for pause menu progression
"""

import pygame  # type: ignore

from .. import runtime_settings, settings
from ..config import (
    BLACK,
    MAIN_MENU_BG_COLOR,
    MAIN_MENU_OPTION_SPACING,
    MAIN_MENU_TITLE_COLOR,
    MAIN_MENU_TITLE_SIZE,
    OVERLAY_DIM_ALPHA,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    WHITE,
)
from ..ui.menu_controller import MenuController
from ..ui.menu_widgets import draw_menu_screen

# Pause-screen layout literals (#433: named inline). Offsets are from the vertical
# centre; the dim overlay reuses config.BLACK at config.OVERLAY_DIM_ALPHA (#450).
PAUSE_TITLE_OFFSET_Y = 120  # "GAME PAUSED" above centre
PAUSE_OPTIONS_OFFSET_Y = 60  # first option row above centre
PAUSE_INSTRUCTIONS_OFFSET_Y = 120  # instruction block below centre
PAUSE_INSTRUCTION_LINE_SPACING = 25
PAUSE_INSTRUCTION_FONT_SIZE = 18

# What a confirmed row maps to, by index. "toggle_minimal_hud" (#977) is handled
# in-place by on_select and returns no action, so the menu stays open on pause.
_ACTIONS = ["resume", "toggle_minimal_hud", "end_match", "return_to_char_select"]


class PauseMenuManager(MenuController):
    """Handles pause menu display and navigation for both players."""

    def __init__(self, p1_controls, p2_controls):
        super().__init__(p1_controls, p2_controls)
        # Index 1 is the minimal-HUD toggle (#977); its label is refreshed live in
        # render(), so the initial string here is just a placeholder for layout width.
        self.options = ["Resume", "Minimal HUD: OFF", "End Match", "Return to Character Select"]

    def _hud_toggle_label(self):
        """The live label for the minimal-HUD toggle row (#977)."""
        return "Minimal HUD: " + ("ON" if runtime_settings.minimal_hud() else "OFF")

    def on_select(self, index):
        action = _ACTIONS[index] if 0 <= index < len(_ACTIONS) else None
        if action == "toggle_minimal_hud":
            # Flip the HUD-declutter setting in place (live + persisted) and stay on the
            # pause menu — no screen transition (mirrors OptionsMenu._activate, #977).
            new = not runtime_settings.minimal_hud()
            runtime_settings.set("minimal_hud", new)
            settings.save({"minimal_hud": new})
            return None
        return action

    def render(self, surface, background_surface=None):
        """Render the pause menu with optional background."""
        # If background surface is provided, draw it first (frozen game state)
        if background_surface:
            surface.blit(background_surface, (0, 0))
        else:
            surface.fill(MAIN_MENU_BG_COLOR)

        # Draw semi-transparent overlay to indicate pause
        pause_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pause_overlay.fill((*BLACK, OVERLAY_DIM_ALPHA))  # Black with ~50% transparency
        surface.blit(pause_overlay, (0, 0))

        # Instructions — pause is a BATTLE state, so its hints obey the show_controls
        # toggle (#681), not the non-battle show_screen_hints one.
        instructions = (
            ["Use W/S or ↑/↓ to navigate", "Press V or / to select"] if runtime_settings.show_controls() else []
        )

        # The minimal-HUD toggle row (#977) shows its live ON/OFF state; the rest are
        # static labels. Rebuilt each frame so a flip is reflected immediately.
        options = list(self.options)
        options[1] = self._hud_toggle_label()

        # Title + glowing button column + instruction lines (#837 shared body). Unlike
        # the main menu, the option spacing is fixed (not font-scaled) and there is no
        # F11 hint; the dim overlay above is the pause-specific pre-step.
        draw_menu_screen(
            surface,
            title="GAME PAUSED",
            title_center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - PAUSE_TITLE_OFFSET_Y),
            title_size=MAIN_MENU_TITLE_SIZE,
            title_color=MAIN_MENU_TITLE_COLOR,
            options=options,
            selected=self.selected_option,
            press_pulse=self.press_pulse,
            options_start_y=SCREEN_HEIGHT // 2 - PAUSE_OPTIONS_OFFSET_Y,
            option_spacing=MAIN_MENU_OPTION_SPACING,
            instructions=instructions,
            instructions_start_y=SCREEN_HEIGHT // 2 + PAUSE_INSTRUCTIONS_OFFSET_Y,
            instruction_font_size=PAUSE_INSTRUCTION_FONT_SIZE,
            instruction_line_spacing=PAUSE_INSTRUCTION_LINE_SPACING,
            instruction_color=WHITE,
        )
