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
from .config import (
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
        
        # Player character selection (which character they've selected, None if not selected)
        self.p1_selected = None
        self.p2_selected = None
        
        # Player confirmation status
        self.p1_confirmed = False
        self.p2_confirmed = False
        
        # Game ready to start (after both confirmed)
        self.show_start_screen = False
        self.start_screen_delay = 0  # Frames to wait before allowing start input
        
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
        
    def reset(self):
        """Reset the character selector to initial state."""
        # Reset cursors
        self.p1_cursor = 0
        self.p2_cursor = 1
        
        # Reset selections
        self.p1_selected = None
        self.p2_selected = None
        
        # Reset confirmations
        self.p1_confirmed = False
        self.p2_confirmed = False
        
        # Reset start screen
        self.show_start_screen = False
        self.start_screen_delay = 0
        
        # Reset input cooldowns
        self.p1_input_cooldown = 0
        self.p2_input_cooldown = 0
        
    def update(self, held_keys, pressed_keys=None):
        """Update character selection based on player input."""
        # If pressed_keys is not provided, fall back to held_keys for backward compatibility
        if pressed_keys is None:
            pressed_keys = held_keys
            
        # Decrease input cooldowns
        if self.p1_input_cooldown > 0:
            self.p1_input_cooldown -= 1
        if self.p2_input_cooldown > 0:
            self.p2_input_cooldown -= 1
        
        # Check if we should show start screen
        if self.both_confirmed() and not self.show_start_screen:
            self.show_start_screen = True
            self.start_screen_delay = 5  # Wait 5 frames before allowing start input
            # Reset input cooldowns when showing start screen to allow immediate input
            self.p1_input_cooldown = 0
            self.p2_input_cooldown = 0
            
        # Decrease start screen delay
        if self.start_screen_delay > 0:
            self.start_screen_delay -= 1
            
        # Handle start screen input
        if self.show_start_screen:
            if self.p1_input_cooldown == 0:
                if self.p1_controls['special'] in pressed_keys:
                    # Go back - unconfirm this player but keep selection
                    self.p1_confirmed = False
                    self.show_start_screen = False
                    self.start_screen_delay = 0
                    self.p1_input_cooldown = 15
                    
            if self.p2_input_cooldown == 0:
                if self.p2_controls['special'] in pressed_keys:
                    # Go back - unconfirm this player but keep selection
                    self.p2_confirmed = False
                    self.show_start_screen = False
                    self.start_screen_delay = 0
                    self.p2_input_cooldown = 15
            # Don't return here - let the main game loop handle A presses for starting
            return
            
        # Handle P1 input (character selection)
        if self.p1_input_cooldown == 0:
            # Movement (only if not confirmed)
            if not self.p1_confirmed:
                if self.p1_controls['left'] in pressed_keys:
                    self.p1_cursor = max(0, self.p1_cursor - 1)
                    self.p1_input_cooldown = 10
                elif self.p1_controls['right'] in pressed_keys:
                    self.p1_cursor = min(len(self.characters) - 1, self.p1_cursor + 1)
                    self.p1_input_cooldown = 10
                elif self.p1_controls['up'] in pressed_keys:
                    new_cursor = self.p1_cursor - CHAR_SELECT_GRID_COLS
                    if new_cursor >= 0:
                        self.p1_cursor = new_cursor
                    self.p1_input_cooldown = 10
                elif self.p1_controls['down'] in pressed_keys:
                    new_cursor = self.p1_cursor + CHAR_SELECT_GRID_COLS
                    if new_cursor < len(self.characters):
                        self.p1_cursor = new_cursor
                    self.p1_input_cooldown = 10
                elif self.p1_controls['attack'] in pressed_keys:
                    # Confirm selection
                    self.p1_selected = self.characters[self.p1_cursor]
                    self.p1_confirmed = True
                    self.p1_input_cooldown = 15
            else:
                # If confirmed, B (special) cancels selection
                if self.p1_controls['special'] in pressed_keys:
                    self.p1_confirmed = False
                    self.p1_selected = None
                    self.p1_input_cooldown = 15
                
        # Handle P2 input (character selection)
        if self.p2_input_cooldown == 0:
            # Movement (only if not confirmed)
            if not self.p2_confirmed:
                if self.p2_controls['left'] in pressed_keys:
                    self.p2_cursor = max(0, self.p2_cursor - 1)
                    self.p2_input_cooldown = 10
                elif self.p2_controls['right'] in pressed_keys:
                    self.p2_cursor = min(len(self.characters) - 1, self.p2_cursor + 1)
                    self.p2_input_cooldown = 10
                elif self.p2_controls['up'] in pressed_keys:
                    new_cursor = self.p2_cursor - CHAR_SELECT_GRID_COLS
                    if new_cursor >= 0:
                        self.p2_cursor = new_cursor
                    self.p2_input_cooldown = 10
                elif self.p2_controls['down'] in pressed_keys:
                    new_cursor = self.p2_cursor + CHAR_SELECT_GRID_COLS
                    if new_cursor < len(self.characters):
                        self.p2_cursor = new_cursor
                    self.p2_input_cooldown = 10
                elif self.p2_controls['attack'] in pressed_keys:
                    # Confirm selection
                    self.p2_selected = self.characters[self.p2_cursor]
                    self.p2_confirmed = True
                    self.p2_input_cooldown = 15
            else:
                # If confirmed, B (special) cancels selection
                if self.p2_controls['special'] in pressed_keys:
                    self.p2_confirmed = False
                    self.p2_selected = None
                    self.p2_input_cooldown = 15
                
    def both_confirmed(self):
        """Check if both players have confirmed their character selection."""
        return self.p1_confirmed and self.p2_confirmed
        
    def get_selected_characters(self):
        """Get the selected characters for both players."""
        return self.p1_selected, self.p2_selected
        
    def can_start_game(self):
        """Check if the game can start (both players confirmed)."""
        return self.both_confirmed()
        
    def ready_to_start(self, pressed_keys):
        """Check if either player pressed A to start the game (only when start screen is shown)."""
        if not self.show_start_screen or self.start_screen_delay > 0:
            return False
        
        # Only start if attack key is pressed (fresh press) AND input cooldown is 0
        can_start = False
        if self.p1_input_cooldown == 0 and self.p1_controls['attack'] in pressed_keys:
            can_start = True
            self.p1_input_cooldown = 15  # Prevent multiple presses
        elif self.p2_input_cooldown == 0 and self.p2_controls['attack'] in pressed_keys:
            can_start = True
            self.p2_input_cooldown = 15  # Prevent multiple presses
            
        return can_start
        
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

        # Create fonts - try to use a Unicode-compatible font
        available_fonts = pygame.font.get_fonts()
        unicode_font_name = None

        # Look for fonts that might support Unicode symbols
        for font_name in ['noto']: # 'arial', 'dejavusans', 'liberation', 'segoe'
            if font_name in available_fonts:
                unicode_font_name = font_name
                break

        # Title
        title_font = pygame.font.SysFont(unicode_font_name, CHAR_SELECT_TITLE_SIZE)
        title_text = title_font.render("Choose Your Cat!", True, CHAR_SELECT_TITLE_COLOR)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 50))
        screen.blit(title_text, title_rect)
        
        # Instructions
        instruction_font = pygame.font.SysFont(unicode_font_name, CHAR_SELECT_INSTRUCTION_SIZE)
        instructions = [
            "Use arrow keys to move cursor",
            "Press A to confirm selection, B to cancel",
            "When both players are ready, either can press A to start"
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
            name_font = pygame.font.SysFont(unicode_font_name, 18)
            name_text = name_font.render(CAT_CHARACTERS[char_key]['name'], True, WHITE)
            name_rect = name_text.get_rect(center=(x + CHAR_SELECT_TILE_SIZE // 2,
                                                  y + CHAR_SELECT_TILE_SIZE + 10))
            screen.blit(name_text, name_rect)
            
        # Draw cursors (only if not confirmed)
        if not self.p1_confirmed:
            self._draw_cursor(screen, self.p1_cursor, (255, 100, 100), "P1", unicode_font_name, large=True)  # Red, large
        if not self.p2_confirmed:
            self._draw_cursor(screen, self.p2_cursor, (100, 100, 255), "P2", unicode_font_name, large=False)  # Blue, small
        
        # Draw selection confirmations
        if self.p1_confirmed and self.p1_selected:
            selected_idx = self.characters.index(self.p1_selected)
            self._draw_confirmation(screen, selected_idx, (255, 100, 100), "P1 ✓", unicode_font_name)
            
        if self.p2_confirmed and self.p2_selected:
            selected_idx = self.characters.index(self.p2_selected)
            self._draw_confirmation(screen, selected_idx, (100, 100, 255), "P2 ✓", unicode_font_name)
            
        # Control instructions at bottom
        self._draw_control_instructions(screen, unicode_font_name)
        
        # Start overlay (if both players are confirmed)
        if self.show_start_screen:
            self._draw_start_overlay(screen, unicode_font_name)
            
    def _draw_cursor(self, screen, cursor_pos, color, label, font_name, large=True):
        """Draw a player's cursor around a tile."""
        x, y = self._grid_pos_to_screen_pos(cursor_pos)
        
        # Different cursor widths based on player
        cursor_width = CHAR_SELECT_CURSOR_WIDTH if large else CHAR_SELECT_CURSOR_WIDTH - 1
        
        # Draw cursor border
        cursor_rect = pygame.Rect(x - cursor_width, 
                                 y - cursor_width,
                                 CHAR_SELECT_TILE_SIZE + 2 * cursor_width,
                                 CHAR_SELECT_TILE_SIZE + 2 * cursor_width)
        pygame.draw.rect(screen, color, cursor_rect, cursor_width)
        
        # Draw player label
        label_font = pygame.font.SysFont(font_name, 16)
        label_text = label_font.render(label, True, color)
        label_rect = label_text.get_rect(center=(x + CHAR_SELECT_TILE_SIZE // 2,
                                                y - 15))
        screen.blit(label_text, label_rect)
        
    def _draw_confirmation(self, screen, char_pos, color, label, font_name):
        """Draw a confirmation checkmark on a selected character."""
        x, y = self._grid_pos_to_screen_pos(char_pos)
        
        # Draw thick border to show selection
        confirm_rect = pygame.Rect(x - 2, y - 2,
                                  CHAR_SELECT_TILE_SIZE + 4,
                                  CHAR_SELECT_TILE_SIZE + 4)
        pygame.draw.rect(screen, color, confirm_rect, 4)
        
        # Draw confirmation label
        confirm_font = pygame.font.SysFont(font_name, 20)
        confirm_text = confirm_font.render(label, True, color)
        confirm_rect = confirm_text.get_rect(center=(x + CHAR_SELECT_TILE_SIZE // 2,
                                                   y + CHAR_SELECT_TILE_SIZE + 30))
        screen.blit(confirm_text, confirm_rect)
        
    def _draw_control_instructions(self, screen, font_name):
        """Draw control instructions at the bottom of the screen."""
        control_font = pygame.font.SysFont(font_name, 16)
        
        # Convert key constants to readable strings
        key_names = {
            pygame.K_a: "A", pygame.K_d: "D", pygame.K_w: "W", pygame.K_s: "S",
            pygame.K_v: "V", pygame.K_c: "C", pygame.K_x: "X",
            pygame.K_LEFT: "←", pygame.K_RIGHT: "→", pygame.K_UP: "↑", pygame.K_DOWN: "↓",
            pygame.K_SLASH: "/", pygame.K_PERIOD: ".", pygame.K_COMMA: ","
        }
        
        # P1 controls
        p1_move_keys = f"{key_names.get(self.p1_controls['left'], '?')}{key_names.get(self.p1_controls['right'], '?')}{key_names.get(self.p1_controls['up'], '?')}{key_names.get(self.p1_controls['down'], '?')}"
        p1_attack_key = key_names.get(self.p1_controls['attack'], '?')
        p1_special_key = key_names.get(self.p1_controls['special'], '?')
        
        p1_text = f"P1: Move({p1_move_keys}) Confirm({p1_attack_key}) Cancel({p1_special_key})"
        p1_surface = control_font.render(p1_text, True, (255, 100, 100))
        p1_rect = p1_surface.get_rect(center=(SCREEN_WIDTH // 4, SCREEN_HEIGHT - 40))
        screen.blit(p1_surface, p1_rect)
        
        # P2 controls
        p2_move_keys = f"{key_names.get(self.p2_controls['left'], '?')}{key_names.get(self.p2_controls['right'], '?')}{key_names.get(self.p2_controls['up'], '?')}{key_names.get(self.p2_controls['down'], '?')}"
        p2_attack_key = key_names.get(self.p2_controls['attack'], '?')
        p2_special_key = key_names.get(self.p2_controls['special'], '?')
        
        p2_text = f"P2: Move({p2_move_keys}) Confirm({p2_attack_key}) Cancel({p2_special_key})"
        p2_surface = control_font.render(p2_text, True, (100, 100, 255))
        p2_rect = p2_surface.get_rect(center=(3 * SCREEN_WIDTH // 4, SCREEN_HEIGHT - 40))
        screen.blit(p2_surface, p2_rect)

    def _draw_start_overlay(self, screen, font_name):
        """Draw the start overlay that partially obscures the grid when both players are confirmed."""
        # Create a semi-transparent overlay
        overlay_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay_surface.set_alpha(128)  # 50% transparency
        overlay_surface.fill((0, 0, 0))
        screen.blit(overlay_surface, (0, 0))
        
        # Calculate center position for the start box
        box_width = 400
        box_height = 150
        box_x = (SCREEN_WIDTH - box_width) // 2
        box_y = (SCREEN_HEIGHT - box_height) // 2
        
        # Draw the start box background
        start_box = pygame.Rect(box_x, box_y, box_width, box_height)
        pygame.draw.rect(screen, (40, 40, 50), start_box)
        pygame.draw.rect(screen, (100, 255, 100), start_box, 3)
        
        # Draw "START" text
        start_font = pygame.font.SysFont(font_name, 48)
        start_text = start_font.render("START", True, (100, 255, 100))
        start_rect = start_text.get_rect(center=(SCREEN_WIDTH // 2, box_y + 40))
        screen.blit(start_text, start_rect)
        
        # Draw instruction text
        instruction_font = pygame.font.SysFont(font_name, 24)
        instruction_text = instruction_font.render("Press A to start the match", True, WHITE)
        instruction_rect = instruction_text.get_rect(center=(SCREEN_WIDTH // 2, box_y + 80))
        screen.blit(instruction_text, instruction_rect)
        
        # Draw cancel instruction
        cancel_text = instruction_font.render("Press B to go back", True, WHITE)
        cancel_rect = cancel_text.get_rect(center=(SCREEN_WIDTH // 2, box_y + 110))
        screen.blit(cancel_text, cancel_rect)
