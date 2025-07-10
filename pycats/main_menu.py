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
    SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK,
    MAIN_MENU_BG_COLOR, MAIN_MENU_TITLE_COLOR, MAIN_MENU_TITLE_SIZE,
    MAIN_MENU_OPTION_SIZE, MAIN_MENU_OPTION_COLOR, MAIN_MENU_SELECTED_COLOR,
    MAIN_MENU_PADDING, MAIN_MENU_OPTION_SPACING
)


class MainMenuManager:
    """Handles main menu display and navigation for both players."""
    
    def __init__(self, p1_controls, p2_controls):
        # Player controls
        self.p1_controls = p1_controls
        self.p2_controls = p2_controls
        
        # Menu options
        self.options = ["Play", "Quit"]
        self.selected_option = 0  # Index of currently selected option
        
        # Input debouncing
        self.input_cooldown = 0
        
        # Action results
        self.action_requested = None  # Will be "play", "quit", or None
        
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
            
        # Handle navigation input from either player
        if (self.p1_controls['up'] in pressed_keys or 
            self.p1_controls['down'] in pressed_keys or
            self.p2_controls['up'] in pressed_keys or 
            self.p2_controls['down'] in pressed_keys):
            
            # Toggle between options (only 2 options, so just flip)
            self.selected_option = 1 - self.selected_option
            self.input_cooldown = 10  # Prevent rapid navigation
            
        # Handle selection input from either player
        if (self.p1_controls['attack'] in pressed_keys or 
            self.p2_controls['attack'] in pressed_keys):
            
            if self.selected_option == 0:  # Play
                self.action_requested = "play"
            elif self.selected_option == 1:  # Quit
                self.action_requested = "quit"
                
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
        
        # Create fonts - try to use a Unicode-compatible font
        available_fonts = pygame.font.get_fonts()
        unicode_font_name = None
        
        # Look for fonts that might support Unicode symbols
        for font_name in ['noto']:  # 'arial', 'dejavusans', 'liberation', 'segoe'
            if font_name in available_fonts:
                unicode_font_name = font_name
                break
        
        title_font = pygame.font.SysFont(unicode_font_name, MAIN_MENU_TITLE_SIZE)
        option_font = pygame.font.SysFont(unicode_font_name, MAIN_MENU_OPTION_SIZE)
        
        # Title
        title_text = title_font.render("Cat Fight", True, MAIN_MENU_TITLE_COLOR)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, MAIN_MENU_PADDING + MAIN_MENU_TITLE_SIZE // 2))
        surface.blit(title_text, title_rect)
        
        # Menu options
        start_y = title_rect.bottom + MAIN_MENU_PADDING
        
        for i, option in enumerate(self.options):
            # Choose color based on selection
            color = MAIN_MENU_SELECTED_COLOR if i == self.selected_option else MAIN_MENU_OPTION_COLOR
            
            option_text = option_font.render(option, True, color)
            option_rect = option_text.get_rect(center=(SCREEN_WIDTH // 2, start_y + i * MAIN_MENU_OPTION_SPACING))
            surface.blit(option_text, option_rect)
            
            # Draw selection indicator
            if i == self.selected_option:
                # Draw arrows on both sides
                arrow_offset = option_text.get_width() // 2 + 20
                left_arrow = option_font.render("►", True, MAIN_MENU_SELECTED_COLOR)
                right_arrow = option_font.render("◄", True, MAIN_MENU_SELECTED_COLOR)
                
                left_pos = (option_rect.centerx - arrow_offset, option_rect.centery - left_arrow.get_height() // 2)
                right_pos = (option_rect.centerx + arrow_offset - right_arrow.get_width(), option_rect.centery - right_arrow.get_height() // 2)
                
                surface.blit(left_arrow, left_pos)
                surface.blit(right_arrow, right_pos)
        
        # Instructions
        instruction_font = pygame.font.SysFont(unicode_font_name, 20)
        instructions = [
            "Use W/S or ↑/↓ to navigate",
            "Press A to select"
        ]
        
        instruction_start_y = SCREEN_HEIGHT - len(instructions) * 30 - MAIN_MENU_PADDING
        
        for i, instruction in enumerate(instructions):
            instruction_text = instruction_font.render(instruction, True, WHITE)
            instruction_rect = instruction_text.get_rect(center=(SCREEN_WIDTH // 2, instruction_start_y + i * 30))
            surface.blit(instruction_text, instruction_rect)
        
        # Draw fullscreen instructions
        fs_text = "F11: Toggle Fullscreen"
        fs_surf = instruction_font.render(fs_text, True, WHITE)
        surface.blit(
            fs_surf,
            (
                SCREEN_WIDTH - fs_surf.get_width() - 10,
                SCREEN_HEIGHT - 25,
            ),
        )
