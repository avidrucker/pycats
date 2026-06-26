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
from . import display
from . import settings
from . import cat_faces
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
# Restore persisted display preferences (#95); defaults if none/invalid.
_prefs = settings.load()

# Open fullscreen if that's how the player last left it.
start_fullscreen = _prefs["fullscreen"]

# Saved windowed-scale preset (1x default; cycle with F10). See pycats.display.
windowed_scale = _prefs["windowed_scale"]
# In-fullscreen magnification (#85, #92): F10 cycles the distinct zoom sizes the
# current monitor can show (display.achievable_zoom_scales). fullscreen_scales is
# that list (set on entering fullscreen); fullscreen_zoom_index points into it.
fullscreen_scales = []
fullscreen_zoom_index = 0
# Transient toast showing the current scale/zoom after an F10 change (#89).
zoom_toast = display.Toast()

if start_fullscreen:
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    display_surface = screen
    game_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

    # Start at the largest achievable zoom ("Fit"), centred in the window.
    fullscreen_scales = display.achievable_zoom_scales(screen.get_size())
    fullscreen_zoom_index = len(fullscreen_scales) - 1
    scale_factor = fullscreen_scales[fullscreen_zoom_index]
    scaled_width, scaled_height = display.window_size_for(scale_factor)
    offset_x = (screen.get_width() - scaled_width) // 2
    offset_y = (screen.get_height() - scaled_height) // 2

    is_fullscreen = True
else:
    # Open the window at the saved scale (offscreen surface + upscale when >1x).
    screen = pygame.display.set_mode(display.window_size_for(windowed_scale))
    display_surface = screen
    game_surface = screen if windowed_scale == 1.0 else pygame.Surface(
        (SCREEN_WIDTH, SCREEN_HEIGHT)
    )
    scale_factor = windowed_scale
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
    jumps = f"{p.fighter.jumps_remaining} jump{'s' if p.fighter.jumps_remaining != 1 else ''} left"
    shield = f"Shield HP: {p.fighter.shield_hp}"
    shield_attempting = f"Shield Attempting: {'Yes' if p.fighter.shield_attempting else 'No'}"
    stocks = f"Lives: {p.fighter.lives}"
    percent = f"Damage: {int(p.fighter.percent)}%"
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
            p.fighter.reset_to_spawn()
            p.fighter.lives = INITIAL_LIVES
            p.fighter.attacks_made = 0
            p.fighter.hits_landed = 0
            p.fighter.suicides = 0
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
    global windowed_scale

    if is_fullscreen:
        # Switch to windowed mode (back to a 1x window)
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        display_surface = screen
        game_surface = screen
        scale_factor = 1.0
        windowed_scale = 1.0
        offset_x = 0
        offset_y = 0
        is_fullscreen = False
        # print("Switched to windowed mode")
    else:
        # Switch to fullscreen at the largest "Fit" zoom; F10 cycles it in place.
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        display_surface = screen
        game_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        is_fullscreen = True
        enter_fullscreen_zoom()


def set_windowed_scale(scale):
    """Switch to windowed mode at `scale`x the 960x540 base (e.g. 1x/1.5x/2x/2.5x).

    The sim always renders at 960x540; at >1x we render to an offscreen
    game_surface and present_frame scales it up to the window. At 1x we render
    straight to the window (no scaling)."""
    global screen, display_surface, game_surface, scale_factor
    global offset_x, offset_y, is_fullscreen, windowed_scale

    windowed_scale = scale
    screen = pygame.display.set_mode(display.window_size_for(scale))
    display_surface = screen
    game_surface = screen if scale == 1.0 else pygame.Surface(
        (SCREEN_WIDTH, SCREEN_HEIGHT)
    )
    scale_factor = scale
    offset_x = 0
    offset_y = 0
    is_fullscreen = False


def enter_fullscreen_zoom():
    """Compute this monitor's distinct zoom sizes and start at the largest ("Fit").
    Call right after switching the display to fullscreen (screen must be active)."""
    global fullscreen_scales, fullscreen_zoom_index
    fullscreen_scales = display.achievable_zoom_scales(screen.get_size())
    set_fullscreen_zoom_index(len(fullscreen_scales) - 1)


def set_fullscreen_zoom_index(i):
    """Apply the i-th achievable fullscreen zoom (staying fullscreen): set the
    magnification of the 960x540 view and recompute the centring offsets. The
    achievable scales already fit the monitor, so the whole stage stays on-screen
    (letterboxed). Assumes the fullscreen display surface is active (screen)."""
    global scale_factor, offset_x, offset_y, fullscreen_zoom_index

    fullscreen_zoom_index = i
    scale_factor = fullscreen_scales[i]
    display_w, display_h = screen.get_size()
    scaled_w, scaled_h = display.window_size_for(scale_factor)
    offset_x = (display_w - scaled_w) // 2
    offset_y = (display_h - scaled_h) // 2


def save_prefs():
    """Persist the current display preferences (#95): windowed scale + fullscreen.
    Called after an F10/F11 change. No-op when persistence is disabled."""
    settings.save({"windowed_scale": windowed_scale, "fullscreen": is_fullscreen})


def get_render_surface():
    """Get the surface to render the game onto (the offscreen 960x540 surface
    whenever we are scaling; the window itself at windowed 1x)."""
    return game_surface


def present_frame():
    """Present the rendered frame to the display."""
    if is_fullscreen:
        # Letterbox: clear, then draw the magnified 960x540 view centred. The
        # zoom (scale_factor) is set by set_fullscreen_zoom_index; crisp at whole
        # multiples, smoothscale at fractional zooms (see display.scale_surface).
        display_surface.fill((0, 0, 0))
        display_surface.blit(
            display.scale_surface(game_surface, scale_factor), (offset_x, offset_y)
        )

    elif game_surface is not screen:
        # Windowed at >1x: scale the offscreen 960x540 surface up to fill the
        # window (which is exactly window_size_for(scale), so no letterbox).
        display_surface.blit(display.scale_surface(game_surface, scale_factor), (0, 0))

    # Zoom toast (#89): drawn on the window surface, above the scene, so it is
    # crisp and screen-positioned (and never lands in the 960x540 sim/goldens).
    if zoom_toast.active:
        text_utils.render_text(
            display_surface,
            zoom_toast.text,
            (display_surface.get_width() - HUD_PADDING, HUD_PADDING),
            24,
            WHITE,
            right_align=True,
        )
    zoom_toast.tick()

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
                save_prefs()
            elif ev.key == pygame.K_ESCAPE and is_fullscreen:
                # Allow ESC to exit fullscreen
                toggle_fullscreen()
                save_prefs()
            elif ev.key == pygame.K_F10:
                if is_fullscreen:
                    # Advance to the next *distinct* achievable zoom (wraps), so
                    # every press visibly changes the rendered size (#92).
                    set_fullscreen_zoom_index(
                        (fullscreen_zoom_index + 1) % len(fullscreen_scales)
                    )
                    scale = fullscreen_scales[fullscreen_zoom_index]
                    zoom_toast.show(
                        display.fullscreen_zoom_label(scale, fullscreen_scales)
                    )
                else:
                    # Windowed: cycle the window-size presets (resizes the window).
                    set_windowed_scale(display.cycle_preset(windowed_scale))
                    zoom_toast.show(display.format_scale_label(windowed_scale))
                    save_prefs()
            elif ev.key == pygame.K_e and player1 is not None:
                # Debug (#108): cycle P1's cat-face style; toast the new style.
                player1.face_style = cat_faces.cycle_face_style(
                    getattr(player1, "face_style", cat_faces.PRIMITIVES)
                )
                zoom_toast.show("P1 face: " + cat_faces.face_style_label(player1.face_style))
            elif ev.key == pygame.K_SEMICOLON and player2 is not None:
                # Debug (#108): cycle P2's cat-face style; toast the new style.
                player2.face_style = cat_faces.cycle_face_style(
                    getattr(player2, "face_style", cat_faces.PRIMITIVES)
                )
                zoom_toast.show("P2 face: " + cat_faces.face_style_label(player2.face_style))

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
        fs_text = (
            "F11: Toggle Fullscreen | "
            + ("F10: Fullscreen Zoom" if is_fullscreen else "F10: Window Size")
            + (" | ESC: Exit Fullscreen" if is_fullscreen else "")
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
        fs_text = (
            "F11: Toggle Fullscreen | "
            + ("F10: Fullscreen Zoom" if is_fullscreen else "F10: Window Size")
            + (" | ESC: Exit Fullscreen" if is_fullscreen else "")
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
