"""
Win screen logic for the cat fighting game.

This module handles:
- Displaying match statistics
- Player confirmation system for viewing stats
- Visual feedback for player confirmations
- Handling input for stats screen progression
"""

import pygame  # type: ignore
from .config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    WHITE,
    BLACK,
    WIN_SCREEN_BG_COLOR,
    WIN_SCREEN_TITLE_SIZE,
    WIN_SCREEN_STATS_SIZE,
    WIN_SCREEN_INSTRUCTION_SIZE,
    WIN_SCREEN_PADDING,
    WIN_SCREEN_LINE_SPACING,
    WIN_SCREEN_TEXT_COLOR,
)
from . import stats_print
from . import text_utils


class WinScreenManager:
    """Handles win screen display and confirmation logic for both players."""

    def __init__(self, p1_controls, p2_controls):
        # Player controls
        self.p1_controls = p1_controls
        self.p2_controls = p2_controls

        # Confirmation status
        self.p1_confirmed = False
        self.p2_confirmed = False

        # Input debouncing
        self.p1_input_cooldown = 0
        self.p2_input_cooldown = 0

        # Delay before returning to character selection
        self.return_delay = 0

        # Match data
        self.winner = None
        self.loser = None
        self.from_pause = False  # Track if we came from pause menu

    def set_match_data(self, winner, loser, from_pause=False):
        """Set the match data for display."""
        self.winner = winner
        self.loser = loser
        self.from_pause = from_pause  # Track if we came from pause menu
        # Reset confirmation status for new match
        self.p1_confirmed = False
        self.p2_confirmed = False
        self.p1_input_cooldown = 0
        self.p2_input_cooldown = 0
        self.return_delay = 0

    def update(self, pressed_keys):
        """Update win screen based on player input."""
        # Decrease input cooldowns
        if self.p1_input_cooldown > 0:
            self.p1_input_cooldown -= 1
        if self.p2_input_cooldown > 0:
            self.p2_input_cooldown -= 1

        # If delay is active, count it down and don't process input
        if self.return_delay > 0:
            self.return_delay -= 1
            return  # Don't process input during delay

        # Handle P1 input
        if self.p1_input_cooldown == 0:
            if self.p1_controls["attack"] in pressed_keys:
                # Confirm viewing stats
                self.p1_confirmed = True
                self.p1_input_cooldown = 15
                # If both players are now confirmed, start the return delay
                if self.p1_confirmed and self.p2_confirmed:
                    self.return_delay = 30  # 30 frames delay
            elif self.p1_controls["special"] in pressed_keys:
                # Cancel confirmation
                self.p1_confirmed = False
                self.p1_input_cooldown = 15

        # Handle P2 input
        if self.p2_input_cooldown == 0:
            if self.p2_controls["attack"] in pressed_keys:
                # Confirm viewing stats
                self.p2_confirmed = True
                self.p2_input_cooldown = 15
                # If both players are now confirmed, start the return delay
                if self.p1_confirmed and self.p2_confirmed:
                    self.return_delay = 30  # 30 frames delay
            elif self.p2_controls["special"] in pressed_keys:
                # Cancel confirmation
                self.p2_confirmed = False
                self.p2_input_cooldown = 15

    def both_confirmed(self):
        """Check if both players have confirmed viewing the stats."""
        return self.p1_confirmed and self.p2_confirmed

    def ready_to_return(self):
        """Check if both players confirmed and the delay has passed."""
        return self.both_confirmed() and self.return_delay == 0

    def render(self, screen):
        """Render the win screen with confirmation indicators."""
        # Clear screen
        screen.fill(WIN_SCREEN_BG_COLOR)

        # Get formatted statistics
        match_summary = stats_print.get_match_summary(self.winner, self.loser, self.from_pause)

        y_offset = WIN_SCREEN_PADDING

        # Winner announcement
        text_utils.render_text(
            screen,
            match_summary["winner_announcement"],
            (SCREEN_WIDTH // 2, y_offset),
            WIN_SCREEN_TITLE_SIZE,
            WIN_SCREEN_TEXT_COLOR,
            center=True,
        )
        y_offset += WIN_SCREEN_LINE_SPACING * 2

        # Final stock count
        text_utils.render_text(
            screen,
            match_summary["final_stocks"],
            (SCREEN_WIDTH // 2, y_offset),
            WIN_SCREEN_STATS_SIZE,
            WIN_SCREEN_TEXT_COLOR,
            center=True,
        )
        y_offset += WIN_SCREEN_LINE_SPACING * 1.5

        # Game statistics header
        text_utils.render_text(
            screen,
            "Game Statistics",
            (SCREEN_WIDTH // 2, y_offset),
            WIN_SCREEN_STATS_SIZE,
            WIN_SCREEN_TEXT_COLOR,
            center=True,
        )
        y_offset += WIN_SCREEN_LINE_SPACING

        # Render the stats table with pixel-perfect positioning
        stats_table_start_y = y_offset
        y_offset = self._render_stats_table(
            screen, match_summary["stats_table"], y_offset
        )

        # Draw confirmation boxes around player columns
        self._draw_confirmation_boxes(screen, stats_table_start_y, y_offset)

        # Instructions
        y_offset += WIN_SCREEN_LINE_SPACING * 2

        # Show different instructions based on confirmation status
        if not self.both_confirmed():
            text_utils.render_text(
                screen,
                "Press A to confirm viewing stats, B to cancel",
                (SCREEN_WIDTH // 2, y_offset),
                WIN_SCREEN_INSTRUCTION_SIZE,
                WIN_SCREEN_TEXT_COLOR,
                center=True,
            )
            y_offset += WIN_SCREEN_LINE_SPACING

            # Show individual player confirmation status with Unicode/ASCII fallback
            p1_status = "✓" if self.p1_confirmed else "..."
            p2_status = "✓" if self.p2_confirmed else "..."

            # Use text_utils with Unicode support and ASCII fallback
            status_text = f"P1: [{p1_status}]    P2: [{p2_status}]"
            text_utils.text_renderer.render_text_mixed(
                status_text,
                WIN_SCREEN_INSTRUCTION_SIZE,
                WIN_SCREEN_TEXT_COLOR,
                screen,
                (SCREEN_WIDTH // 2, y_offset),
                center=True,
            )
        else:
            # Both confirmed, show return instruction
            text_utils.render_text(
                screen,
                "Both players ready - returning to character selection...",
                (SCREEN_WIDTH // 2, y_offset),
                WIN_SCREEN_INSTRUCTION_SIZE,
                WIN_SCREEN_TEXT_COLOR,
                center=True,
            )

    def _render_stats_table(self, screen, stats_table, start_y):
        """Render the stats table with pixel-perfect column alignment."""
        # Column widths in pixels
        stat_col_width = 180  # Width for stat names
        player_col_width = 100  # Width for player columns
        col_spacing = 20  # Space between columns

        # Calculate column positions
        center_x = SCREEN_WIDTH // 2
        total_width = stat_col_width + (2 * player_col_width) + (2 * col_spacing)
        table_start_x = center_x - (total_width // 2)

        # Column X positions
        stat_col_x = table_start_x
        p1_col_x = stat_col_x + stat_col_width + col_spacing
        p2_col_x = p1_col_x + player_col_width + col_spacing

        # Store column positions for confirmation boxes
        self.table_columns = {
            "stat_col_x": stat_col_x,
            "stat_col_width": stat_col_width,
            "p1_col_x": p1_col_x,
            "p1_col_width": player_col_width,
            "p2_col_x": p2_col_x,
            "p2_col_width": player_col_width,
        }

        current_y = start_y

        # Render header
        header = stats_table["header"]

        # Stat label (right-aligned)
        text_utils.render_text(
            screen,
            header["stat_label"],
            (stat_col_x + stat_col_width, current_y),
            WIN_SCREEN_STATS_SIZE,
            WIN_SCREEN_TEXT_COLOR,
            right_align=True,
        )

        # P1 label (center-aligned)
        text_utils.render_text(
            screen,
            header["p1_label"],
            (p1_col_x + player_col_width // 2, current_y),
            WIN_SCREEN_STATS_SIZE,
            WIN_SCREEN_TEXT_COLOR,
            center=True,
        )

        # P2 label (center-aligned)
        text_utils.render_text(
            screen,
            header["p2_label"],
            (p2_col_x + player_col_width // 2, current_y),
            WIN_SCREEN_STATS_SIZE,
            WIN_SCREEN_TEXT_COLOR,
            center=True,
        )

        current_y += WIN_SCREEN_LINE_SPACING

        # Render separator line
        line_color = WIN_SCREEN_TEXT_COLOR
        pygame.draw.line(
            screen,
            line_color,
            (stat_col_x, current_y),
            (stat_col_x + stat_col_width, current_y),
            2,
        )
        pygame.draw.line(
            screen,
            line_color,
            (p1_col_x, current_y),
            (p1_col_x + player_col_width, current_y),
            2,
        )
        pygame.draw.line(
            screen,
            line_color,
            (p2_col_x, current_y),
            (p2_col_x + player_col_width, current_y),
            2,
        )

        current_y += WIN_SCREEN_LINE_SPACING * 0.5

        # Render data rows
        for row in stats_table["rows"]:
            # Stat name (right-aligned)
            text_utils.render_text(
                screen,
                row["stat_name"],
                (stat_col_x + stat_col_width, current_y),
                WIN_SCREEN_STATS_SIZE,
                WIN_SCREEN_TEXT_COLOR,
                right_align=True,
            )

            # P1 value (center-aligned)
            text_utils.render_text(
                screen,
                row["p1_value"],
                (p1_col_x + player_col_width // 2, current_y),
                WIN_SCREEN_STATS_SIZE,
                WIN_SCREEN_TEXT_COLOR,
                center=True,
            )

            # P2 value (center-aligned)
            text_utils.render_text(
                screen,
                row["p2_value"],
                (p2_col_x + player_col_width // 2, current_y),
                WIN_SCREEN_STATS_SIZE,
                WIN_SCREEN_TEXT_COLOR,
                center=True,
            )

            current_y += WIN_SCREEN_LINE_SPACING * 0.8

        return current_y

    def _draw_confirmation_boxes(self, screen, table_start_y, table_end_y):
        """Draw colored boxes around player columns to show confirmation status."""
        # Use the stored column positions from _render_stats_table
        if not hasattr(self, "table_columns"):
            return  # Table hasn't been rendered yet

        columns = self.table_columns

        # Box dimensions
        box_padding = 10
        box_height = table_end_y - table_start_y + box_padding * 2

        # Draw P1 confirmation box (red)
        if self.p1_confirmed:
            p1_rect = pygame.Rect(
                columns["p1_col_x"] - box_padding,
                table_start_y - box_padding,
                columns["p1_col_width"] + box_padding * 2,
                box_height,
            )
            pygame.draw.rect(screen, (255, 100, 100), p1_rect, 4)  # Red border

        # Draw P2 confirmation box (blue)
        if self.p2_confirmed:
            p2_rect = pygame.Rect(
                columns["p2_col_x"] - box_padding,
                table_start_y - box_padding,
                columns["p2_col_width"] + box_padding * 2,
                box_height,
            )
            pygame.draw.rect(screen, (100, 100, 255), p2_rect, 4)  # Blue border
