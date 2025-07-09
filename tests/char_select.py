"""
Character selection screen logic for the cat fighting game.

This module handles:
- Rendering the character selection grid
- Player cursor movement and selection
- Token pickup/drop mechanics
- Character preview rendering
"""

import pygame
import math
from ..pycats.config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    CHAR_SELECT_BG_COLOR, CHAR_SELECT_TITLE_COLOR, CHAR_SELECT_TITLE_SIZE,
    CHAR_SELECT_INSTRUCTION_SIZE, CHAR_SELECT_PADDING, CHAR_SELECT_GRID_COLS,
    CHAR_SELECT_GRID_ROWS, CHAR_SELECT_TILE_SIZE, CHAR_SELECT_TILE_SPACING,
    CHAR_SELECT_CURSOR_COLOR, CHAR_SELECT_CURSOR_WIDTH, CHAR_SELECT_TOKEN_SIZE,
    CHAR_SELECT_TOKEN_BORDER_WIDTH, CAT_CHARACTERS,
    EYE_OFFSET_X, EYE_OFFSET_Y, EYE_RADIUS, GLINT_OFFSET_X, GLINT_OFFSET_Y,
    GLINT_RADIUS, EAR_WIDTH, EAR_HEIGHT, EAR_SPACING, EAR_PADDING,
    WHISKER_LENGTH, WHISKER_THICKNESS, WHISKER_COUNT, WHISKER_ANGLE,
    WHISKER_OFFSET_Y, WHISKER_OFFSET_X, STRIPE_COUNT, STRIPE_WIDTH,
    STRIPE_HEIGHT, STRIPE_SPACING, WHITE, BLACK
)


class CharacterSelector:
    """Handles character selection screen logic for both players."""
    
    def __init__(self, p1_controls, p2_controls):
        # Character list in order
        self.characters = list(CAT_CHARACTERS.keys())
        
        # Player cursors (grid positions)
        self.p1_cursor = 0  # grid index
        self.p2_cursor = 1  # grid index
        
        # Player tokens (which character they've selected, None if not selected)
        self.p1_token = None
        self.p2_token = None
        
        # Player controls
        self.p1_controls = p1_controls
        self.p2_controls = p2_controls
        
        # Input debouncing
        self.p1_input_cooldown = 0
        self.p2_input_cooldown = 0
        
        # Grid layout
        self.grid_start_x = (SCREEN_WIDTH - (CHAR_SELECT_GRID_COLS * CHAR_SELECT_TILE_SIZE + 
                                            (CHAR_SELECT_GRID_COLS - 1) * CHAR_SELECT_TILE_SPACING)) // 2
        self.grid_start_y = 150  # Below title
        
    def update(self, held_keys):
        """Update character selection based on player input."""
        # Decrease input cooldowns
        if self.p1_input_cooldown > 0:
            self.p1_input_cooldown -= 1
        if self.p2_input_cooldown > 0:
            self.p2_input_cooldown -= 1
            
        # Handle P1 input
        if self.p1_input_cooldown == 0:
            if self.p1_controls['left'] in held_keys:
                self.p1_cursor = max(0, self.p1_cursor - 1)
                self.p1_input_cooldown = 10
            elif self.p1_controls['right'] in held_keys:
                self.p1_cursor = min(len(self.characters) - 1, self.p1_cursor + 1)
                self.p1_input_cooldown = 10
            elif self.p1_controls['up'] in held_keys:
                new_cursor = self.p1_cursor - CHAR_SELECT_GRID_COLS
                if new_cursor >= 0:
                    self.p1_cursor = new_cursor
                self.p1_input_cooldown = 10
            elif self.p1_controls['down'] in held_keys:
                new_cursor = self.p1_cursor + CHAR_SELECT_GRID_COLS
                if new_cursor < len(self.characters):
                    self.p1_cursor = new_cursor
                self.p1_input_cooldown = 10
            elif self.p1_controls['attack'] in held_keys:
                self._handle_p1_token_action()
                self.p1_input_cooldown = 15
                
        # Handle P2 input
        if self.p2_input_cooldown == 0:
            if self.p2_controls['left'] in held_keys:
                self.p2_cursor = max(0, self.p2_cursor - 1)
                self.p2_input_cooldown = 10
            elif self.p2_controls['right'] in held_keys:
                self.p2_cursor = min(len(self.characters) - 1, self.p2_cursor + 1)
                self.p2_input_cooldown = 10
            elif self.p2_controls['up'] in held_keys:
                new_cursor = self.p2_cursor - CHAR_SELECT_GRID_COLS
                if new_cursor >= 0:
                    self.p2_cursor = new_cursor
                self.p2_input_cooldown = 10
            elif self.p2_controls['down'] in held_keys:
                new_cursor = self.p2_cursor + CHAR_SELECT_GRID_COLS
                if new_cursor < len(self.characters):
                    self.p2_cursor = new_cursor
                self.p2_input_cooldown = 10
            elif self.p2_controls['attack'] in held_keys:
                self._handle_p2_token_action()
                self.p2_input_cooldown = 15
                
    def _handle_p1_token_action(self):
        """Handle P1 token pickup/drop."""
        if self.p1_token is None:
            # Pick up token at current cursor
            self.p1_token = self.characters[self.p1_cursor]
        else:
            # Drop token at current cursor
            self.p1_token = None
            
    def _handle_p2_token_action(self):
        """Handle P2 token pickup/drop."""
        if self.p2_token is None:
            # Pick up token at current cursor
            self.p2_token = self.characters[self.p2_cursor]
        else:
            # Drop token at current cursor
            self.p2_token = None
            
    def both_ready(self):
        """Check if both players have selected characters."""
        return self.p1_token is not None and self.p2_token is not None
        
    def get_selected_characters(self):
        """Get the selected characters for both players."""
        return self.p1_token, self.p2_token
        
    def _grid_pos_to_screen_pos(self, grid_index):
        """Convert grid index to screen position."""
        col = grid_index % CHAR_SELECT_GRID_COLS
        row = grid_index // CHAR_SELECT_GRID_COLS
        
        x = self.grid_start_x + col * (CHAR_SELECT_TILE_SIZE + CHAR_SELECT_TILE_SPACING)
        y = self.grid_start_y + row * (CHAR_SELECT_TILE_SIZE + CHAR_SELECT_TILE_SPACING)
        
        return x, y
        
    def _draw_cat_preview(self, screen, char_key, x, y, size):
        """Draw a small cat preview in the given tile."""
        char_data = CAT_CHARACTERS[char_key]
        
        # Scale down for preview
        preview_size = (size * 0.6, size * 0.8)
        cat_rect = pygame.Rect(x + (size - preview_size[0]) // 2,
                              y + (size - preview_size[1]) // 2,
                              preview_size[0], preview_size[1])
        
        # Draw body
        pygame.draw.rect(screen, char_data['color'], cat_rect)
        
        # Draw stripes (simplified)
        if char_data['stripe_color'] != char_data['color']:
            stripe_height = preview_size[1] // 6
            for i in range(3):
                stripe_y = cat_rect.y + i * stripe_height * 2
                stripe_rect = pygame.Rect(cat_rect.x, stripe_y, preview_size[0], stripe_height)
                pygame.draw.rect(screen, char_data['stripe_color'], stripe_rect)
        
        # Draw ears
        ear_width = preview_size[0] // 6
        ear_height = preview_size[1] // 4
        left_ear = pygame.Rect(cat_rect.x + ear_width // 2, cat_rect.y - ear_height // 2,
                              ear_width, ear_height)
        right_ear = pygame.Rect(cat_rect.x + preview_size[0] - ear_width * 1.5,
                               cat_rect.y - ear_height // 2, ear_width, ear_height)
        pygame.draw.rect(screen, char_data['color'], left_ear)
        pygame.draw.rect(screen, char_data['color'], right_ear)
        
        # Draw eyes
        eye_size = max(2, int(preview_size[0] // 12))
        left_eye_pos = (cat_rect.x + preview_size[0] // 3,
                       cat_rect.y + preview_size[1] // 4)
        right_eye_pos = (cat_rect.x + 2 * preview_size[0] // 3,
                        cat_rect.y + preview_size[1] // 4)
        
        pygame.draw.circle(screen, char_data['eye_color'], left_eye_pos, eye_size)
        pygame.draw.circle(screen, char_data['eye_color'], right_eye_pos, eye_size)
        
        # Draw eye glints
        glint_size = max(1, eye_size // 2)
        pygame.draw.circle(screen, WHITE, 
                          (left_eye_pos[0] + 1, left_eye_pos[1] - 1), glint_size)
        pygame.draw.circle(screen, WHITE,
                          (right_eye_pos[0] + 1, right_eye_pos[1] - 1), glint_size)
        
    def render(self, screen):
        """Render the character selection screen."""
        # Clear screen
        screen.fill(CHAR_SELECT_BG_COLOR)
        
        # Title
        title_font = pygame.font.SysFont(None, CHAR_SELECT_TITLE_SIZE)
        title_text = title_font.render("Choose Your Cat!", True, CHAR_SELECT_TITLE_COLOR)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 50))
        screen.blit(title_text, title_rect)
        
        # Instructions
        instruction_font = pygame.font.SysFont(None, CHAR_SELECT_INSTRUCTION_SIZE)
        instructions = [
            "Use arrow keys to move cursor",
            "Press attack button to pick up/drop token",
            "Both players must select a character to continue"
        ]
        
        for i, instruction in enumerate(instructions):
            text = instruction_font.render(instruction, True, CHAR_SELECT_TITLE_COLOR)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, 100 + i * 20))
            screen.blit(text, text_rect)
        
        # Character grid
        for i, char_key in enumerate(self.characters):
            x, y = self._grid_pos_to_screen_pos(i)
            
            # Draw tile background
            tile_rect = pygame.Rect(x, y, CHAR_SELECT_TILE_SIZE, CHAR_SELECT_TILE_SIZE)
            pygame.draw.rect(screen, (50, 50, 60), tile_rect)
            pygame.draw.rect(screen, WHITE, tile_rect, 1)
            
            # Draw cat preview
            self._draw_cat_preview(screen, char_key, x, y, CHAR_SELECT_TILE_SIZE)
            
            # Draw character name
            name_font = pygame.font.SysFont(None, 18)
            name_text = name_font.render(CAT_CHARACTERS[char_key]['name'], True, WHITE)
            name_rect = name_text.get_rect(center=(x + CHAR_SELECT_TILE_SIZE // 2,
                                                  y + CHAR_SELECT_TILE_SIZE + 10))
            screen.blit(name_text, name_rect)
            
        # Draw cursors
        self._draw_cursor(screen, self.p1_cursor, (255, 100, 100), "P1")  # Red
        self._draw_cursor(screen, self.p2_cursor, (100, 100, 255), "P2")  # Blue
        
        # Draw tokens
        if self.p1_token is not None:
            token_char_idx = self.characters.index(self.p1_token)
            self._draw_token(screen, token_char_idx, (255, 100, 100), "P1")
            
        if self.p2_token is not None:
            token_char_idx = self.characters.index(self.p2_token)
            self._draw_token(screen, token_char_idx, (100, 100, 255), "P2")
            
        # Ready indicator
        if self.both_ready():
            ready_font = pygame.font.SysFont(None, 32)
            ready_text = ready_font.render("Both players ready! Press any key to start...", 
                                         True, (100, 255, 100))
            ready_rect = ready_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30))
            screen.blit(ready_text, ready_rect)
            
    def _draw_cursor(self, screen, cursor_pos, color, label):
        """Draw a player's cursor around a tile."""
        x, y = self._grid_pos_to_screen_pos(cursor_pos)
        
        # Draw cursor border
        cursor_rect = pygame.Rect(x - CHAR_SELECT_CURSOR_WIDTH, 
                                 y - CHAR_SELECT_CURSOR_WIDTH,
                                 CHAR_SELECT_TILE_SIZE + 2 * CHAR_SELECT_CURSOR_WIDTH,
                                 CHAR_SELECT_TILE_SIZE + 2 * CHAR_SELECT_CURSOR_WIDTH)
        pygame.draw.rect(screen, color, cursor_rect, CHAR_SELECT_CURSOR_WIDTH)
        
        # Draw player label
        label_font = pygame.font.SysFont(None, 16)
        label_text = label_font.render(label, True, color)
        label_rect = label_text.get_rect(center=(x + CHAR_SELECT_TILE_SIZE // 2,
                                                y - 15))
        screen.blit(label_text, label_rect)
        
    def _draw_token(self, screen, token_pos, color, label):
        """Draw a player's token on a tile."""
        x, y = self._grid_pos_to_screen_pos(token_pos)
        
        # Draw token as a circle in the corner
        token_x = x + CHAR_SELECT_TILE_SIZE - CHAR_SELECT_TOKEN_SIZE - 5
        token_y = y + 5
        
        pygame.draw.circle(screen, color, (token_x, token_y), CHAR_SELECT_TOKEN_SIZE)
        pygame.draw.circle(screen, WHITE, (token_x, token_y), CHAR_SELECT_TOKEN_SIZE, 
                          CHAR_SELECT_TOKEN_BORDER_WIDTH)
        
        # Draw label inside token
        token_font = pygame.font.SysFont(None, 12)
        token_text = token_font.render(label, True, WHITE)
        token_text_rect = token_text.get_rect(center=(token_x, token_y))
        screen.blit(token_text, token_text_rect)
