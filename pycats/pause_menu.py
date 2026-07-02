"""
Pause menu screen logic for the cat fighting game.

This module handles:
- Displaying the pause menu with game options
- Menu navigation and selection during pause
- Visual feedback for menu options
- Handling input for pause menu progression
"""

import pygame  # type: ignore
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


class PauseMenuManager:
    """Handles pause menu display and navigation for both players."""

    def __init__(self, p1_controls, p2_controls):
        # Player controls
        self.p1_controls = p1_controls
        self.p2_controls = p2_controls

        # Menu options
        self.options = ["Resume", "End Match", "Return to Menu"]
        self.selected_option = 0  # Index of currently selected option

        # Input debouncing
        self.input_cooldown = 0

        # Action results
        self.action_requested = None  # Will be "resume", "end_match", "return_to_menu", or None

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

        # Handle navigation input from either player (up/down)
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

        # Handle selection input from either player (/ or V keys only)
        if (
            pygame.K_SLASH in pressed_keys  # P2's attack key
            or pygame.K_v in pressed_keys     # P1's attack key
        ):
            if self.selected_option == 0:  # Resume
                self.action_requested = "resume"
            elif self.selected_option == 1:  # End Match
                self.action_requested = "end_match"
            elif self.selected_option == 2:  # Return to Menu
                self.action_requested = "return_to_menu"

            self.input_cooldown = 20  # Prevent rapid selection

    def get_action(self):
        """Get the requested action and clear it."""
        action = self.action_requested
        self.action_requested = None
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
        pause_overlay.fill((0, 0, 0, 128))  # Black with 50% transparency
        surface.blit(pause_overlay, (0, 0))

        # Title
        text_renderer.render_text_simple(
            "GAME PAUSED",
            MAIN_MENU_TITLE_SIZE,
            MAIN_MENU_TITLE_COLOR,
            surface,
            (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 120),
            center=True,
        )

        # Menu options — the shared glowing menu-button widget (#359/#360): a coloured
        # rect that glows when focused with a redundant ► marker (focus not colour-only,
        # #346), replacing the old per-option colour + ►◄ arrows. Reads well over the
        # dimmed game background (unfocused rows are outline-only).
        start_y = SCREEN_HEIGHT // 2 - 60

        for i, option in enumerate(self.options):
            option_y = start_y + i * MAIN_MENU_OPTION_SPACING
            draw_menu_button(
                surface,
                option,
                (SCREEN_WIDTH // 2, option_y),
                MAIN_MENU_OPTION_SIZE,
                focused=(i == self.selected_option),
            )

        # Instructions
        instructions = [
            "Use W/S or ↑/↓ to navigate",
            "Press V or / to select"
        ]

        instruction_start_y = SCREEN_HEIGHT // 2 + 120

        for i, instruction in enumerate(instructions):
            instruction_y = instruction_start_y + i * 25
            text_renderer.render_text_mixed(
                instruction,
                18,
                WHITE,
                surface,
                (SCREEN_WIDTH // 2, instruction_y),
                center=True,
            )
