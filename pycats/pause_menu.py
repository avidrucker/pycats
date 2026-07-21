"""
Pause menu screen logic for the cat fighting game.

This module handles:
- Displaying the pause menu with game options
- Menu navigation and selection during pause
- Visual feedback for menu options
- Handling input for pause menu progression
"""

import pygame  # type: ignore

from . import runtime_settings
from .config import (
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
from .menu_controller import MenuController
from .menu_widgets import draw_menu_screen

# Pause-screen layout literals (#433: named inline). Offsets are from the vertical
# centre; the dim overlay reuses config.BLACK at config.OVERLAY_DIM_ALPHA (#450).
PAUSE_TITLE_OFFSET_Y = 120  # "GAME PAUSED" above centre
PAUSE_OPTIONS_OFFSET_Y = 60  # first option row above centre
PAUSE_INSTRUCTIONS_OFFSET_Y = 120  # instruction block below centre
PAUSE_INSTRUCTION_LINE_SPACING = 25
PAUSE_INSTRUCTION_FONT_SIZE = 18

# What a confirmed row maps to, by index.
_ACTIONS = ["resume", "end_match", "return_to_char_select"]


class PauseMenuManager(MenuController):
    """Handles pause menu display and navigation for both players."""

    def __init__(self, p1_controls, p2_controls):
        super().__init__(p1_controls, p2_controls)
        self.options = ["Resume", "End Match", "Return to Character Select"]

    def on_select(self, index):
        return _ACTIONS[index] if 0 <= index < len(_ACTIONS) else None

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

        # Title + glowing button column + instruction lines (#837 shared body). Unlike
        # the main menu, the option spacing is fixed (not font-scaled) and there is no
        # F11 hint; the dim overlay above is the pause-specific pre-step.
        draw_menu_screen(
            surface,
            title="GAME PAUSED",
            title_center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - PAUSE_TITLE_OFFSET_Y),
            title_size=MAIN_MENU_TITLE_SIZE,
            title_color=MAIN_MENU_TITLE_COLOR,
            options=self.options,
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
