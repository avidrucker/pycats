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
from .entities import Platform
from .core import input as inp
from . import stats_print
from .screen_manager import ScreenStateManager
from .battle_screen import BattleScreen
from .render_battle import draw_shell_chrome
from . import text_utils
from . import display
from . import settings
from . import runtime_settings
from . import cat_faces

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
# Battle state + per-frame sim are owned by BattleScreen (#193); game.py reads
# battle.player1/player2/players/attacks instead of module globals.
battle = BattleScreen(P1_KEYS, P2_KEYS)

# ------------------------------------------------ pygame set-up
# Restore persisted display preferences (#95); defaults if none/invalid.
_prefs = settings.load()
# Seed the live present-layer settings (#121) so the render path reads the saved
# HUD toggles immediately; the Options sub-menu mutates this live.
runtime_settings.seed(_prefs)

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
def reset_game():
    """Reset the battle for a new match (delegates to BattleScreen, #193)."""
    battle.reset()


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

# Display hooks for the Options sub-menu (#121): reuse the F10/F11 machinery so a
# menu change applies live AND persists (save_prefs), just like the hotkeys. Read
# the module globals at call time (they're reassigned by the setters).
def _opt_cycle_windowed_scale():
    set_windowed_scale(display.cycle_preset(windowed_scale))
    save_prefs()


def _opt_toggle_fullscreen():
    toggle_fullscreen()
    save_prefs()


_display_hooks = {
    "get_windowed_scale": lambda: windowed_scale,
    "cycle_windowed_scale": _opt_cycle_windowed_scale,
    "is_fullscreen": lambda: is_fullscreen,
    "toggle_fullscreen": _opt_toggle_fullscreen,
}

# Screen state manager
screen_manager = ScreenStateManager(P1_KEYS, P2_KEYS, display_hooks=_display_hooks)

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
            elif ev.key == pygame.K_e and battle.player1 is not None:
                # Debug (#108): cycle P1's cat-face style; toast the new style.
                battle.player1.face_style = cat_faces.cycle_face_style(
                    getattr(battle.player1, "face_style", cat_faces.PRIMITIVES)
                )
                zoom_toast.show("P1 face: " + cat_faces.face_style_label(battle.player1.face_style))
            elif ev.key == pygame.K_SEMICOLON and battle.player2 is not None:
                # Debug (#108): cycle P2's cat-face style; toast the new style.
                battle.player2.face_style = cat_faces.cycle_face_style(
                    getattr(battle.player2, "face_style", cat_faces.PRIMITIVES)
                )
                zoom_toast.show("P2 face: " + cat_faces.face_style_label(battle.player2.face_style))

    # Update screen state manager. `platforms` is threaded so the playing state's
    # engine action owns the per-frame battle.step + winner-set (#246).
    screen_manager.update(frame_input, battle, platforms)

    # Check if we should quit
    if screen_manager.should_quit_game():
        running = False
        continue

    # Check if we should return to main menu (ESC-hold from playing)
    if screen_manager.should_return_to_menu():
        screen_manager.esc_quit_to_menu = False
        screen_manager.should_quit = False
        # Reset game state and transition to main menu
        reset_game()
        screen_manager.reset_to_main_menu()
        continue

    current_state = screen_manager.get_state()
    # (#230) The pause->win_screen stats wiring + char_select reset are now engine
    # entry/update actions (screen_manager._on_enter_win_screen / _update_char_select),
    # fed by the battle threaded into the engine ctx above — the previous_state loop
    # hack and the should_reset_game poll are retired.

    if current_state == "main_menu":
        # Render main menu
        screen_manager.render(get_render_surface())

    elif current_state == "char_select":
        # (#230) battle reset on char-select-with-no-winner moved to
        # screen_manager._update_char_select (engine action).
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
        # The per-frame update (player creation, battle.step, winner-set) is owned by
        # the playing state's engine action (screen_manager._update_playing, #246),
        # which ran above in screen_manager.update — the loop body only renders now.
        # ---- render: battle composite + 'P: Pause Game' hint owned by BattleScreen
        # (#205 slice 2b, #279); the shell overlays (FPS/fullscreen/debug) read loop
        # state — not battle state — so they live in a render helper the loop calls
        # (#279), keeping shell state out of the battle object (cf. #100 Risks, #246).
        render_surface = get_render_surface()
        battle.render(render_surface, platforms)
        draw_shell_chrome(render_surface, clock.get_fps(), is_fullscreen, frame_input)
        screen_manager.render_esc_quit_progress(render_surface)

    elif current_state == "pause":
        # Game is paused — BattleScreen composites the frozen battle background and
        # delegates to the pause menu (#205 slice 2b).
        battle.render_paused(
            get_render_surface(), platforms, screen_manager.get_pause_menu()
        )

    elif current_state == "win_screen":
        # Render win screen
        screen_manager.render(get_render_surface())

    present_frame()

pygame.quit()
sys.exit()
