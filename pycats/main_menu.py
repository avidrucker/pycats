"""
Main menu screen logic for the cat fighting game.

This module handles:
- Displaying the title screen with game options
- Menu navigation and selection
- Visual feedback for menu options
- Handling input for menu progression
"""

from . import runtime_settings
from .config import (
    MAIN_MENU_BG_COLOR,
    MAIN_MENU_OPTION_SPACING,
    MAIN_MENU_PADDING,
    MAIN_MENU_TITLE_COLOR,
    MAIN_MENU_TITLE_SIZE,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    WHITE,
)
from .menu_controller import MenuController
from .menu_widgets import draw_menu_screen
from .text_utils import text_renderer

# Layout literals for the instruction/fullscreen-hint text (#433: named inline).
INSTRUCTION_FONT_SIZE = 20  # bottom navigation-hint lines
INSTRUCTION_LINE_SPACING = 30  # vertical stride between hint lines
FS_HINT_FONT_SIZE = 20  # the "F11: Toggle Fullscreen" hint
FS_HINT_MARGIN_X = 10  # right margin of the fullscreen hint
FS_HINT_MARGIN_BOTTOM = 25  # bottom margin of the fullscreen hint

# What a confirmed row maps to (drives the screen FSM transitions).
_ACTIONS = {"Play": "play", "Options": "options", "Quit": "quit"}


class MainMenuManager(MenuController):
    """Handles main menu display and navigation for both players."""

    def __init__(self, p1_controls, p2_controls):
        super().__init__(p1_controls, p2_controls)
        self.options = ["Play", "Options", "Quit"]

    def on_select(self, index):
        return _ACTIONS.get(self.options[index])

    def render(self, surface):
        """Render the main menu."""
        # Clear screen
        surface.fill(MAIN_MENU_BG_COLOR)

        # Menu options spacing scales with the live font_scale (#402).
        scale = runtime_settings.font_scale()
        spacing = round(MAIN_MENU_OPTION_SPACING * scale)
        start_y = MAIN_MENU_PADDING + MAIN_MENU_TITLE_SIZE + MAIN_MENU_PADDING

        # Per-screen action hints (#681) — gated by the non-battle show_screen_hints
        # toggle. The hold-ESC-to-quit line (the #549 hidden affordance) only appears
        # while that affordance is enabled, so a disabled ESC never mis-advertises.
        instructions = []
        instruction_start_y = 0
        if runtime_settings.show_screen_hints():
            instructions = ["Use W/S or ↑/↓ to navigate", "Press A (/ or V) to select"]
            if runtime_settings.esc_hold_to_navigate():
                instructions.append("Hold ESC to quit")
            instruction_start_y = SCREEN_HEIGHT - len(instructions) * INSTRUCTION_LINE_SPACING - MAIN_MENU_PADDING

        # Title + glowing button column + instruction lines (#837 shared body). The
        # widget owns the focus visual (#359/#360): a coloured rect that glows when
        # focused with a redundant ► marker (focus not colour-only, #346).
        draw_menu_screen(
            surface,
            title="Cat Fight",
            title_center=(SCREEN_WIDTH // 2, MAIN_MENU_PADDING + MAIN_MENU_TITLE_SIZE // 2),
            title_size=MAIN_MENU_TITLE_SIZE,
            title_color=MAIN_MENU_TITLE_COLOR,
            options=self.options,
            selected=self.selected_option,
            press_pulse=self.press_pulse,
            options_start_y=start_y,
            option_spacing=spacing,
            instructions=instructions,
            instructions_start_y=instruction_start_y,
            instruction_font_size=INSTRUCTION_FONT_SIZE,
            instruction_line_spacing=INSTRUCTION_LINE_SPACING,
            instruction_color=WHITE,
        )

        # Draw fullscreen instructions
        fs_text = "F11: Toggle Fullscreen"
        fs_font = text_renderer.sys_font(None, FS_HINT_FONT_SIZE)
        fs_surf = fs_font.render(fs_text, True, WHITE)
        surface.blit(
            fs_surf,
            (SCREEN_WIDTH - fs_surf.get_width() - FS_HINT_MARGIN_X, SCREEN_HEIGHT - FS_HINT_MARGIN_BOTTOM),
        )
