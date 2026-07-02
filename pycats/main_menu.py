"""
Main menu screen logic for the cat fighting game.

This module handles:
- Displaying the title screen with game options
- Menu navigation and selection
- Visual feedback for menu options
- Handling input for menu progression
"""

import pygame
from .config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    WHITE,
    BLACK,
    MAIN_MENU_BG_COLOR,
    MAIN_MENU_TITLE_COLOR,
    MAIN_MENU_TITLE_SIZE,
    MAIN_MENU_OPTION_SIZE,
    MAIN_MENU_PADDING,
    MAIN_MENU_OPTION_SPACING,
)
from .text_utils import text_renderer
from .menu_widgets import draw_menu_button
from . import runtime_settings


class MainMenuManager:
    """Handles main menu display and navigation for both players."""

    def __init__(self, p1_controls, p2_controls):
        # Player controls
        self.p1_controls = p1_controls
        self.p2_controls = p2_controls

        # Menu options
        self.options = ["Play", "Options", "Quit"]
        self.selected_option = 0  # Index of currently selected option

        # Input debouncing
        self.input_cooldown = 0

        # Action results
        self.action_requested = None  # Will be "play", "options", "quit", or None

    def reset(self):
        """Reset the menu state."""
        self.selected_option = 0
        self.input_cooldown = 0
        self.action_requested = None

    def update(self, pressed_keys):
        """Update menu based on player input."""
        # Decrease input cooldown
        if self.input_cooldown > 0:
            self.input_cooldown -= 1

        # Don't process input during cooldown
        if self.input_cooldown > 0:
            return

        # Handle navigation input from either player (wraps over N options)
        if (
            self.p1_controls["up"] in pressed_keys
            or self.p2_controls["up"] in pressed_keys
        ):
            self.selected_option = (self.selected_option - 1) % len(self.options)
            self.input_cooldown = 10  # Prevent rapid navigation

        if (
            self.p1_controls["down"] in pressed_keys
            or self.p2_controls["down"] in pressed_keys
        ):
            self.selected_option = (self.selected_option + 1) % len(self.options)
            self.input_cooldown = 10  # Prevent rapid navigation

        # Handle selection input from either player
        if (
            self.p1_controls["attack"] in pressed_keys
            or self.p2_controls["attack"] in pressed_keys
        ):
            self.action_requested = {
                "Play": "play",
                "Options": "options",
                "Quit": "quit",
            }.get(self.options[self.selected_option])

            self.input_cooldown = 20  # Prevent rapid selection

    def get_action(self):
        """Get the requested action and clear it."""
        action = self.action_requested
        self.action_requested = None
        return action

    def render(self, surface):
        """Render the main menu."""
        # Clear screen
        surface.fill(MAIN_MENU_BG_COLOR)

        # Title
        text_renderer.render_text_simple(
            "Cat Fight",
            MAIN_MENU_TITLE_SIZE,
            MAIN_MENU_TITLE_COLOR,
            surface,
            (SCREEN_WIDTH // 2, MAIN_MENU_PADDING + MAIN_MENU_TITLE_SIZE // 2),
            center=True,
        )

        # Menu options — the shared glowing menu-button widget (#359/#360): a coloured
        # rect that glows when focused with a redundant ► marker (focus not colour-only,
        # #346). Spacing scales with the live font_scale (#402). The widget owns the
        # focus visual, replacing the old per-option colour + ►◄ arrows.
        scale = runtime_settings.font_scale()
        spacing = round(MAIN_MENU_OPTION_SPACING * scale)
        start_y = MAIN_MENU_PADDING + MAIN_MENU_TITLE_SIZE + MAIN_MENU_PADDING

        for i, option in enumerate(self.options):
            option_y = start_y + i * spacing
            draw_menu_button(
                surface,
                option,
                (SCREEN_WIDTH // 2, option_y),
                MAIN_MENU_OPTION_SIZE,
                focused=(i == self.selected_option),
            )

        # Instructions - use mixed rendering for the arrow symbols
        instructions = ["Use W/S or ↑/↓ to navigate", "Press A (/ or V) to select"]

        instruction_start_y = SCREEN_HEIGHT - len(instructions) * 30 - MAIN_MENU_PADDING

        for i, instruction in enumerate(instructions):
            instruction_y = instruction_start_y + i * 30
            text_renderer.render_text_mixed(
                instruction,
                20,
                WHITE,
                surface,
                (SCREEN_WIDTH // 2, instruction_y),
                center=True,
            )

        # Draw fullscreen instructions
        fs_text = "F11: Toggle Fullscreen"
        fs_font = text_renderer.sys_font(None, 20)
        fs_surf = fs_font.render(fs_text, True, WHITE)
        surface.blit(
            fs_surf, (SCREEN_WIDTH - fs_surf.get_width() - 10, SCREEN_HEIGHT - 25)
        )
