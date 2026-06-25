"""
Purpose: Main game loop and top-level orchestration.

Contents:
- Initializes Pygame and window.
- Creates players, platforms, and attack sprite groups.
- Runs the game loop (handling input, updating, rendering).
- Renders eye, shield bubble, HUD.

Use: This is the entry point for running the game.
"""

#### DONE: implement game pause w/ P key press (IMPLEMENTED - pause with P, resume with P/V/)
#### DONE: implement win screen when one player runs out of stocks
#### TODO: implement menu options for pause screen such as restart, quit, etc.
#### TODO: increase player jump height, and increase thin platforms height
#### TODO: implement coyote time where players can, for a single frame after leaving the ledge, still have 2 jumps
#### TODO: fix bug where players can jump sideways through the thick platform

# ------------------------------------------------ stage & sprites
#### TODO: implement stage selection w/ various platform layouts (NOT YET)
#### TODO: implement player pushing & sliding where players can push each other left/right (if both players are pushing on each other, there is no horizontal movement, else, there is slowed movement in the pushed direction) and when one lands on the other they also get pushed apart and the bottom character gets their vertical velocity downward increased if they are both in the air and the top character gets their vertical velocity upward increased with a short hop/bounce up

import sys
import pygame  # type: ignore
from .config import *  #### TODO: replace all global imports with specific imports from config.py (READY)

# Also explicitly import the new cat feature constants
from .config import (
    EAR_WIDTH,
    EAR_HEIGHT,
    EAR_SPACING,
    EAR_PADDING,
    WHISKER_LENGTH,
    WHISKER_THICKNESS,
    WHISKER_COUNT,
    WHISKER_ANGLE,
    WHISKER_OFFSET_Y,
    WHISKER_OFFSET_X,
    STRIPE_COUNT,
    STRIPE_WIDTH,
    STRIPE_HEIGHT,
    STRIPE_SPACING,
    CAT_CHARACTERS,
)
from .entities import Platform, Player
from .systems import combat
from .systems.win_condition import winner_loser
from .core import input as inp
from .core.physics import resolve_player_push
from . import stats_print
from .screen_manager import ScreenStateManager
from . import text_utils
from .render_battle import render_battle, render_attacks

pygame.init()
pygame.display.set_caption("PyCats - Smash-Draft Rev 6 (fsm)")

# Rect: (x, y, width, height)
platforms = [
    Platform(
        pygame.Rect(
            THICK_PLAT_DICT["x"],
            THICK_PLAT_DICT["y"],
            THICK_PLAT_DICT["w"],
            THICK_PLAT_DICT["h"],
        ),
        thin=False,
    ),
    Platform(
        pygame.Rect(
            THIN_PLAT_DICT_L["x"],
            THIN_PLAT_DICT_L["y"],
            THIN_PLAT_DICT_L["w"],
            THIN_PLAT_DICT_L["h"],
        ),
        thin=True,
    ),
    Platform(
        pygame.Rect(
            THIN_PLAT_DICT_R["x"],
            THIN_PLAT_DICT_R["y"],
            THIN_PLAT_DICT_R["w"],
            THIN_PLAT_DICT_R["h"],
        ),
        thin=True,
    ),
]

P1_KEYS = dict(
    left=pygame.K_a,
    right=pygame.K_d,
    up=pygame.K_w,
    down=pygame.K_s,
    attack=pygame.K_v,
    special=pygame.K_c,
    shield=pygame.K_x,
)
P2_KEYS = dict(
    left=pygame.K_LEFT,
    right=pygame.K_RIGHT,
    up=pygame.K_UP,
    down=pygame.K_DOWN,
    attack=pygame.K_SLASH,
    special=pygame.K_PERIOD,
    shield=pygame.K_COMMA,
)

# Players will be created after character selection
player1 = None
player2 = None
players = pygame.sprite.Group()
attacks = pygame.sprite.Group()

# ------------------------------------------------ pygame set-up
# Start in windowed mode by default (change to True for fullscreen by default)
start_fullscreen = False

if start_fullscreen:
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    display_surface = screen
    game_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

    # Calculate scaling for fullscreen
    screen_width, screen_height = screen.get_size()
    scale_x = screen_width / SCREEN_WIDTH
    scale_y = screen_height / SCREEN_HEIGHT

    # For crisp scaling, prefer integer scale factors when possible
    max_integer_scale = min(int(scale_x), int(scale_y))
    if max_integer_scale >= 1:
        # Use integer scaling for crisp pixels
        scale_factor = float(max_integer_scale)
    else:
        # If screen is smaller than game resolution, use fractional scaling
        scale_factor = min(scale_x, scale_y)

    scaled_width = int(SCREEN_WIDTH * scale_factor)
    scaled_height = int(SCREEN_HEIGHT * scale_factor)
    offset_x = (screen_width - scaled_width) // 2
    offset_y = (screen_height - scaled_height) // 2

    is_fullscreen = True
else:
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    display_surface = screen
    game_surface = screen
    scale_factor = 1.0
    offset_x = 0
    offset_y = 0
    is_fullscreen = False

clock = pygame.time.Clock()

# Create fonts - try to use a Unicode-compatible font
available_fonts = pygame.font.get_fonts()
unicode_font_name = None

#### QUICK FONT TEST
# cheese = True if 'cheese' not in locals() else False

# if cheese:
#     for font in available_fonts:
#         if 'symbol' in font.lower():
#             print(f"Found symbol font: {font}")
#     cheese = False
####

# Look for fonts that might support Unicode symbols
for font_name in [
    "segoeuisymbol",
    "fonts-seto",
    "notosanssymbols",
]:  # 'arial', 'dejavusans', 'liberation', 'segoe'
    if font_name in available_fonts:
        unicode_font_name = font_name
        break

font = pygame.font.SysFont(unicode_font_name, 24)


# ------------------------------------------------ helpers
# Battle draw helpers (draw_eye, draw_cat_features, draw_stripes,
# draw_player_name) and render_battle/render_attacks now live in
# pycats/render_battle.py so the live game, pause screen, and sim presenters
# share one renderer.


#### TODO: split off damage % and stock lives rendering so that they are rendering last and at the bottom left and right corners of the screen
#### TODO: implement dev info bool flag that, when True, shows all infos, and when False, only shows what should be shown to players normally
def draw_hud(surface, p: Player, label, topright=False):
    """Draws the HUD for a player, showing their state, jumps left, shield HP, lives, and damage percent."""
    fsm = f"FSM: {p.state.capitalize()}"
    jumps = f"{p.jumps_remaining} jump{'s' if p.jumps_remaining != 1 else ''} left"
    shield = f"Shield HP: {p.shield_hp}"
    shield_attempting = f"Shield Attempting: {'Yes' if p.shield_attempting else 'No'}"
    stocks = f"Lives: {p.lives}"
    percent = f"Damage: {int(p.percent)}%"
    for i, txt in enumerate(
        (label, fsm, jumps, shield, shield_attempting, stocks, percent)
    ):
        x_pos = SCREEN_WIDTH - HUD_PADDING if topright else HUD_PADDING
        y_pos = HUD_PADDING + i * HUD_SPACING

        text_utils.render_text(
            surface, txt, (x_pos, y_pos), 24, WHITE, right_align=topright
        )


def draw_controls(surface, p: Player, label, topright=False):
    """Draws the control scheme for a player below the HUD."""
    # Convert pygame key constants to readable strings with Unicode arrows where appropriate
    key_names = {
        pygame.K_a: "A",
        pygame.K_d: "D",
        pygame.K_w: "W",
        pygame.K_s: "S",
        pygame.K_v: "V",
        pygame.K_c: "C",
        pygame.K_x: "X",
        pygame.K_LEFT: "←",
        pygame.K_RIGHT: "→",
        pygame.K_UP: "↑",
        pygame.K_DOWN: "↓",
        pygame.K_SLASH: "/",
        pygame.K_PERIOD: ".",
        pygame.K_COMMA: ",",
    }

    controls = [
        f"{label} Controls:",
        f"Move: {key_names.get(p.controls['left'], '?')}/{key_names.get(p.controls['right'], '?')}",
        f"Jump: {key_names.get(p.controls['up'], '?')}",
        f"Down: {key_names.get(p.controls['down'], '?')}",
        f"Attack: {key_names.get(p.controls['attack'], '?')}",
        f"Shield: {key_names.get(p.controls['shield'], '?')}",
        f"Special: {key_names.get(p.controls['special'], '?')}",
    ]

    # Start drawing below the HUD (7 lines of HUD + some spacing)
    start_y = HUD_PADDING + 7 * HUD_SPACING + 20

    for i, txt in enumerate(controls):
        x_pos = SCREEN_WIDTH - HUD_PADDING if topright else HUD_PADDING
        y_pos = start_y + i * HUD_SPACING

        # Use mixed text rendering for Unicode arrow support
        if topright:
            # For right-aligned text, we need to calculate positioning differently
            text_width = text_utils.text_renderer._get_font(None, 24).size(txt)[0]
            adjusted_x = x_pos - text_width
            text_utils.text_renderer.render_text_mixed(
                txt, 24, WHITE, surface, (adjusted_x, y_pos)
            )
        else:
            text_utils.text_renderer.render_text_mixed(
                txt, 24, WHITE, surface, (x_pos, y_pos)
            )


def reset_game():
    """Reset the game state for a new match"""
    global player1, player2, players, attacks

    # Only reset if players exist (they may not exist if coming from character selection)
    if player1 and player2:
        # Per-life/spawn state is owned by Player.reset_to_spawn() (#34) so the
        # new-match path and the per-life respawn cannot drift. reset_game adds
        # only the match-scoped resets: full lives, cleared statistics, and a
        # hard FSM reset to idle (the per-life respawn lets the chart transition
        # ko -> idle on its own instead).
        for p in (player1, player2):
            p.reset_to_spawn()
            p.lives = INITIAL_LIVES
            p.attacks_made = 0
            p.hits_landed = 0
            p.suicides = 0
            p.engine.force("idle")

    # Clear all attacks
    attacks.empty()


def check_win_condition():
    """(winner, loser) or (None, None) — delegates to the single win-condition
    rule (systems.win_condition), shared with the headless match_engine."""
    return winner_loser((player1, player2))


def toggle_fullscreen():
    """Toggle between fullscreen and windowed mode."""
    global screen, is_fullscreen, display_surface, game_surface, scale_factor, offset_x, offset_y

    if is_fullscreen:
        # Switch to windowed mode
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        display_surface = screen
        game_surface = screen
        scale_factor = 1.0
        offset_x = 0
        offset_y = 0
        is_fullscreen = False
        # print("Switched to windowed mode")
    else:
        # Switch to fullscreen mode
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        display_surface = screen

        # Create a surface for rendering the game at original resolution
        game_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

        # Calculate scaling to fit the screen while maintaining aspect ratio
        screen_width, screen_height = screen.get_size()
        scale_x = screen_width / SCREEN_WIDTH
        scale_y = screen_height / SCREEN_HEIGHT

        # For crisp scaling, prefer integer scale factors when possible
        max_integer_scale = min(int(scale_x), int(scale_y))
        if max_integer_scale >= 1:
            # Use integer scaling for crisp pixels
            scale_factor = float(max_integer_scale)
        else:
            # If screen is smaller than game resolution, use fractional scaling
            scale_factor = min(scale_x, scale_y)

        # Calculate offset to center the scaled image
        scaled_width = int(SCREEN_WIDTH * scale_factor)
        scaled_height = int(SCREEN_HEIGHT * scale_factor)
        offset_x = (screen_width - scaled_width) // 2
        offset_y = (screen_height - scaled_height) // 2

        is_fullscreen = True
        # print(f"Switched to fullscreen mode: {screen_width}x{screen_height}, scale: {scale_factor:.2f}")
        # print(f"Using {'integer' if scale_factor == int(scale_factor) else 'fractional'} scaling")


def get_render_surface():
    """Get the surface to render the game onto."""
    return game_surface if is_fullscreen else screen


def present_frame():
    """Present the rendered frame to the display."""
    if is_fullscreen:
        # Clear the display surface
        display_surface.fill((0, 0, 0))

        # Scale and blit the game surface to the display using nearest-neighbor for crisp scaling
        scaled_width = int(SCREEN_WIDTH * scale_factor)
        scaled_height = int(SCREEN_HEIGHT * scale_factor)

        # For crisp pixel art scaling, we want to use integer scaling when possible
        # and avoid sub-pixel positioning
        if scale_factor >= 2.0 and scale_factor == int(scale_factor):
            # Perfect integer scaling - use scale_by for best results
            try:
                scaled_surface = pygame.transform.scale_by(
                    game_surface, int(scale_factor)
                )
            except AttributeError:
                # Fallback for older pygame versions
                scaled_surface = pygame.transform.scale(
                    game_surface, (scaled_width, scaled_height)
                )
        else:
            # For non-integer scaling, still use regular scale but with size adjustment
            # to maintain crisp pixels as much as possible
            scaled_surface = pygame.transform.scale(
                game_surface, (scaled_width, scaled_height)
            )

        display_surface.blit(scaled_surface, (offset_x, offset_y))

    pygame.display.flip()


# ------------------------------------------------ main loop
running = True

# Screen state manager
screen_manager = ScreenStateManager(P1_KEYS, P2_KEYS)

# Game state
winner = None
loser = None


def create_players_from_selection():
    """Create players based on character selection"""
    global player1, player2, players

    p1_char, p2_char = screen_manager.get_selected_characters()

    # Get character data from config
    p1_data = CAT_CHARACTERS[p1_char]
    p2_data = CAT_CHARACTERS[p2_char]

    # Create players with selected characters; default to the statechart engine.
    # Override with PYCATS_STATE_BACKEND=legacy for the frozen classic baseline.
    import os as _os
    _backend = _os.environ.get("PYCATS_STATE_BACKEND", "statechart")
    player1 = Player(
        PLAYER1_START_X,
        PLAYER1_START_Y,
        P1_KEYS,
        p1_data["color"],
        eye_color=p1_data["eye_color"],
        char_name="P1",  # Use player ID instead of character name
        facing_right=True,
        state_backend=_backend,
    )

    player2 = Player(
        PLAYER2_START_X,
        PLAYER2_START_Y,
        P2_KEYS,
        p2_data["color"],
        eye_color=p2_data["eye_color"],
        char_name="P2",  # Use player ID instead of character name
        facing_right=False,
        state_backend=_backend,
    )

    # Update stripe colors based on character selection
    player1.stripe_color = p1_data["stripe_color"]
    player2.stripe_color = p2_data["stripe_color"]

    # Recreate player group
    players = pygame.sprite.Group(player1, player2)


while running:
    dt = clock.tick(FPS)
    frame_input, events = inp.poll()

    for ev in events:
        if ev.type == pygame.QUIT:
            running = False
        elif ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_F11:
                toggle_fullscreen()
            elif ev.key == pygame.K_ESCAPE and is_fullscreen:
                # Allow ESC to exit fullscreen
                toggle_fullscreen()

    # Update screen state manager
    screen_manager.update(frame_input)

    # Check if we should quit
    if screen_manager.should_quit_game():
        running = False
        continue

    current_state = screen_manager.get_state()
    
    # Track previous state to detect transitions
    if 'previous_state' not in locals():
        previous_state = current_state
    
    # Handle state transitions
    if previous_state == "pause" and current_state == "win_screen":
        # Transitioning from pause to win screen (stats view)
        if player1 and player2:
            screen_manager.set_stats_data(player1, player2)
    
    previous_state = current_state

    if current_state == "main_menu":
        # Render main menu
        screen_manager.render(get_render_surface())

    elif current_state == "char_select":
        # Check if we need to reset the game (coming from win screen)
        if screen_manager.should_reset_game():
            reset_game()

        # Render character selection
        screen_manager.render(get_render_surface())

        # Draw fullscreen instructions on character select screen
        fs_text = "F11: Toggle Fullscreen" + (
            " | ESC: Exit Fullscreen" if is_fullscreen else ""
        )
        text_utils.render_text(
            get_render_surface(),
            fs_text,
            (SCREEN_WIDTH - HUD_PADDING, SCREEN_HEIGHT - HUD_SPACING),
            24,
            WHITE,
            right_align=True,
        )

        # Draw back to menu instruction
        back_text = "Hold B for 1 second to return to main menu"
        text_utils.render_text(
            get_render_surface(),
            back_text,
            (HUD_PADDING, SCREEN_HEIGHT - HUD_SPACING),
            24,
            WHITE,
        )

    elif current_state == "playing":
        # Check if we need to create players (first time entering playing state)
        if player1 is None or player2 is None:
            create_players_from_selection()

        # ---- update
        for p in players:
            p.update(frame_input, platforms, attacks)
        resolve_player_push(list(players))
        attacks.update()
        combat.process_hits(players, attacks)

        # Check for win condition
        winner, loser = check_win_condition()
        if winner:
            screen_manager.set_winner(winner, loser)

        # ---- render
        render_surface = get_render_surface()
        render_surface.fill(BG_COLOR)
        render_battle(render_surface, players, platforms)
        render_attacks(render_surface, attacks)

        # Draw HUD only if players exist
        if player1 and player2:
            draw_hud(
                render_surface, player1, "P1"
            )  # drawn by default in upper-left corner
            draw_hud(render_surface, player2, "P2", topright=True)

            # Draw player controls below the HUD
            draw_controls(
                render_surface, player1, "P1"
            )  # drawn by default below P1 HUD
            draw_controls(
                render_surface, player2, "P2", topright=True
            )  # drawn below P2 HUD

        # draw keys pressed for debugging
        if frame_input:
            # keys = ", ".join(
            #     f"{k}: {v}" for k, v in frame_input.items() if v
            # )
            text_utils.render_text(
                render_surface,
                frame_input.__str__(),
                (HUD_PADDING, SCREEN_HEIGHT - HUD_SPACING),
                24,
                WHITE,
            )
        # draw FPS and fullscreen instructions
        text_utils.render_text(
            render_surface,
            f"FPS: {clock.get_fps():.2f}",
            (SCREEN_WIDTH - HUD_PADDING, SCREEN_HEIGHT - HUD_SPACING),
            24,
            WHITE,
            right_align=True,
        )

        # Draw fullscreen instructions
        fs_text = "F11: Toggle Fullscreen" + (
            " | ESC: Exit Fullscreen" if is_fullscreen else ""
        )
        text_utils.render_text(
            render_surface,
            fs_text,
            (SCREEN_WIDTH - HUD_PADDING, SCREEN_HEIGHT - HUD_SPACING * 2),
            24,
            WHITE,
            right_align=True,
        )

        # Draw pause instruction
        text_utils.render_text(
            render_surface,
            "P: Pause Game",
            (SCREEN_WIDTH - HUD_PADDING, SCREEN_HEIGHT - HUD_SPACING * 3),
            24,
            WHITE,
            right_align=True,
        )

    elif current_state == "pause":
        # Game is paused - render the pause menu with frozen game background
        render_surface = get_render_surface()
        
        # Create background surface with frozen game state
        background_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        background_surface.fill(BG_COLOR)
        
        # Draw the game state (frozen) to background
        render_battle(background_surface, players, platforms)
        render_attacks(background_surface, attacks)

        # Draw HUD (frozen state)
        if player1 and player2:
            draw_hud(background_surface, player1, "P1")
            draw_hud(background_surface, player2, "P2", topright=True)

        # Render pause menu with background
        pause_menu = screen_manager.get_pause_menu()
        pause_menu.render(render_surface, background_surface)

    elif current_state == "win_screen":
        # Render win screen
        screen_manager.render(get_render_surface())

    present_frame()

pygame.quit()
sys.exit()
