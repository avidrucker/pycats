"""
Win screen logic for the cat fighting game.

This module handles:
- Displaying match statistics
- Player confirmation system for viewing stats
- Visual feedback for player confirmations
- Handling input for stats screen progression
"""

import pygame
from .config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK,
    WIN_SCREEN_BG_COLOR, WIN_SCREEN_TITLE_SIZE, WIN_SCREEN_STATS_SIZE,
    WIN_SCREEN_INSTRUCTION_SIZE, WIN_SCREEN_PADDING, WIN_SCREEN_LINE_SPACING,
    WIN_SCREEN_TEXT_COLOR
)
from . import stats_print


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
        
    def set_match_data(self, winner, loser):
        """Set the match data for display."""
        self.winner = winner
        self.loser = loser
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
            if self.p1_controls['attack'] in pressed_keys:
                # Confirm viewing stats
                self.p1_confirmed = True
                self.p1_input_cooldown = 15
                # If both players are now confirmed, start the return delay
                if self.p1_confirmed and self.p2_confirmed:
                    self.return_delay = 30  # 30 frames delay
            elif self.p1_controls['special'] in pressed_keys:
                # Cancel confirmation
                self.p1_confirmed = False
                self.p1_input_cooldown = 15
                
        # Handle P2 input
        if self.p2_input_cooldown == 0:
            if self.p2_controls['attack'] in pressed_keys:
                # Confirm viewing stats
                self.p2_confirmed = True
                self.p2_input_cooldown = 15
                # If both players are now confirmed, start the return delay
                if self.p1_confirmed and self.p2_confirmed:
                    self.return_delay = 30  # 30 frames delay
            elif self.p2_controls['special'] in pressed_keys:
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
        match_summary = stats_print.get_match_summary(self.winner, self.loser)
        
        # Create fonts
        title_font = pygame.font.SysFont(None, WIN_SCREEN_TITLE_SIZE)
        stats_font = pygame.font.SysFont(None, WIN_SCREEN_STATS_SIZE)
        instruction_font = pygame.font.SysFont(None, WIN_SCREEN_INSTRUCTION_SIZE)
        
        y_offset = WIN_SCREEN_PADDING
        
        # Winner announcement
        winner_text = title_font.render(match_summary['winner_announcement'], True, WIN_SCREEN_TEXT_COLOR)
        winner_rect = winner_text.get_rect(centerx=SCREEN_WIDTH // 2, y=y_offset)
        screen.blit(winner_text, winner_rect)
        y_offset += WIN_SCREEN_LINE_SPACING * 2
        
        # Final stock count
        stocks_text = stats_font.render(match_summary['final_stocks'], True, WIN_SCREEN_TEXT_COLOR)
        stocks_rect = stocks_text.get_rect(centerx=SCREEN_WIDTH // 2, y=y_offset)
        screen.blit(stocks_text, stocks_rect)
        y_offset += WIN_SCREEN_LINE_SPACING * 1.5
        
        # Game statistics header
        stats_header = stats_font.render("Game Statistics", True, WIN_SCREEN_TEXT_COLOR)
        stats_rect = stats_header.get_rect(centerx=SCREEN_WIDTH // 2, y=y_offset)
        screen.blit(stats_header, stats_rect)
        y_offset += WIN_SCREEN_LINE_SPACING
        
        # Render the stats table with pixel-perfect positioning
        stats_table_start_y = y_offset
        y_offset = self._render_stats_table(screen, match_summary['stats_table'], stats_font, y_offset)
        
        # Draw confirmation boxes around player columns
        self._draw_confirmation_boxes(screen, stats_table_start_y, y_offset, stats_font)
        
        # Instructions
        y_offset += WIN_SCREEN_LINE_SPACING * 2
        
        # Show different instructions based on confirmation status
        if not self.both_confirmed():
            instruction_text = instruction_font.render("Press A to confirm viewing stats, B to cancel", True, WIN_SCREEN_TEXT_COLOR)
            instruction_rect = instruction_text.get_rect(centerx=SCREEN_WIDTH // 2, y=y_offset)
            screen.blit(instruction_text, instruction_rect)
            y_offset += WIN_SCREEN_LINE_SPACING
            
            # Show individual player confirmation status
            p1_status = "✓" if self.p1_confirmed else "..."
            p2_status = "✓" if self.p2_confirmed else "..."
            
            status_text = instruction_font.render(f"P1: {p1_status}    P2: {p2_status}", True, WIN_SCREEN_TEXT_COLOR)
            status_rect = status_text.get_rect(centerx=SCREEN_WIDTH // 2, y=y_offset)
            screen.blit(status_text, status_rect)
        else:
            # Both confirmed, show return instruction
            return_text = instruction_font.render("Both players ready - returning to character selection...", True, WIN_SCREEN_TEXT_COLOR)
            return_rect = return_text.get_rect(centerx=SCREEN_WIDTH // 2, y=y_offset)
            screen.blit(return_text, return_rect)
            
    def _render_stats_table(self, screen, stats_table, font, start_y):
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
            'stat_col_x': stat_col_x,
            'stat_col_width': stat_col_width,
            'p1_col_x': p1_col_x,
            'p1_col_width': player_col_width,
            'p2_col_x': p2_col_x,
            'p2_col_width': player_col_width
        }
        
        current_y = start_y
        
        # Render header
        header = stats_table['header']
        
        # Stat label (right-aligned)
        stat_label = font.render(header['stat_label'], True, WIN_SCREEN_TEXT_COLOR)
        stat_rect = stat_label.get_rect(right=stat_col_x + stat_col_width, y=current_y)
        screen.blit(stat_label, stat_rect)
        
        # P1 label (center-aligned)
        p1_label = font.render(header['p1_label'], True, WIN_SCREEN_TEXT_COLOR)
        p1_rect = p1_label.get_rect(centerx=p1_col_x + player_col_width // 2, y=current_y)
        screen.blit(p1_label, p1_rect)
        
        # P2 label (center-aligned)
        p2_label = font.render(header['p2_label'], True, WIN_SCREEN_TEXT_COLOR)
        p2_rect = p2_label.get_rect(centerx=p2_col_x + player_col_width // 2, y=current_y)
        screen.blit(p2_label, p2_rect)
        
        current_y += WIN_SCREEN_LINE_SPACING
        
        # Render separator line
        line_color = WIN_SCREEN_TEXT_COLOR
        pygame.draw.line(screen, line_color, 
                        (stat_col_x, current_y), 
                        (stat_col_x + stat_col_width, current_y), 2)
        pygame.draw.line(screen, line_color, 
                        (p1_col_x, current_y), 
                        (p1_col_x + player_col_width, current_y), 2)
        pygame.draw.line(screen, line_color, 
                        (p2_col_x, current_y), 
                        (p2_col_x + player_col_width, current_y), 2)
        
        current_y += WIN_SCREEN_LINE_SPACING * 0.5
        
        # Render data rows
        for row in stats_table['rows']:
            # Stat name (right-aligned)
            stat_text = font.render(row['stat_name'], True, WIN_SCREEN_TEXT_COLOR)
            stat_rect = stat_text.get_rect(right=stat_col_x + stat_col_width, y=current_y)
            screen.blit(stat_text, stat_rect)
            
            # P1 value (center-aligned)
            p1_text = font.render(row['p1_value'], True, WIN_SCREEN_TEXT_COLOR)
            p1_rect = p1_text.get_rect(centerx=p1_col_x + player_col_width // 2, y=current_y)
            screen.blit(p1_text, p1_rect)
            
            # P2 value (center-aligned)
            p2_text = font.render(row['p2_value'], True, WIN_SCREEN_TEXT_COLOR)
            p2_rect = p2_text.get_rect(centerx=p2_col_x + player_col_width // 2, y=current_y)
            screen.blit(p2_text, p2_rect)
            
            current_y += WIN_SCREEN_LINE_SPACING * 0.8
        
        return current_y
            
    def _draw_confirmation_boxes(self, screen, table_start_y, table_end_y, stats_font):
        """Draw colored boxes around player columns to show confirmation status."""
        # Use the stored column positions from _render_stats_table
        if not hasattr(self, 'table_columns'):
            return  # Table hasn't been rendered yet
            
        columns = self.table_columns
        
        # Box dimensions
        box_padding = 10
        box_height = table_end_y - table_start_y + box_padding * 2
        
        # Draw P1 confirmation box (red)
        if self.p1_confirmed:
            p1_rect = pygame.Rect(
                columns['p1_col_x'] - box_padding, 
                table_start_y - box_padding, 
                columns['p1_col_width'] + box_padding * 2, 
                box_height
            )
            pygame.draw.rect(screen, (255, 100, 100), p1_rect, 4)  # Red border
            
        # Draw P2 confirmation box (blue)
        if self.p2_confirmed:
            p2_rect = pygame.Rect(
                columns['p2_col_x'] - box_padding, 
                table_start_y - box_padding,
                columns['p2_col_width'] + box_padding * 2, 
                box_height
            )
            pygame.draw.rect(screen, (100, 100, 255), p2_rect, 4)  # Blue border
