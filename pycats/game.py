"""
Purpose: Main game loop and top-level orchestration.

Contents:
- Initializes Pygame and window.
- Creates players, platforms, and attack sprite groups.
- Runs the game loop (handling input, updating, rendering).
- Renders eye, shield bubble, HUD.

Use: This is the entry point for running the game.
"""

#### TODO: implement game pause w/ P key press (READY)
#### TODO: implement win screen when one player runs out of stocks
#### TODO: implement menu options for pause screen such as restart, quit, etc.
#### TODO: increase player jump height, and increase thin platforms height
#### TODO: implement hurt state where, if a player is hit with an attack and they recieve damage, that they flash red, and cannot attack or jump for a short duration (e.g. 0.5 seconds), and then return to normal state
#### TODO: implement coyote time where players can, for a single frame after leaving the ledge, still have 2 jumps

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
from .core import input as inp
from .core.physics import resolve_player_push
from . import stats_print
from .screen_manager import ScreenStateManager

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

# Look for fonts that might support Unicode symbols
for font_name in ['noto']: # 'arial', 'dejavusans', 'liberation', 'segoe'
    if font_name in available_fonts:
        unicode_font_name = font_name
        break

font = pygame.font.SysFont(unicode_font_name, 24)

# ------------------------------------------------ helpers
def draw_eye(surface, p: Player, eye=True):
    if eye:
        x = p.rect.right - EYE_OFFSET_X if p.facing_right else p.rect.left + EYE_OFFSET_X
        y = p.rect.top + EYE_OFFSET_Y
        pygame.draw.circle(surface, p.eye_color, (x, y), EYE_RADIUS)
    else: # we will draw a glint instead of an eye
        x = p.rect.right - GLINT_OFFSET_X if p.facing_right else p.rect.left + GLINT_OFFSET_X
        y = p.rect.top + GLINT_OFFSET_Y
        pygame.draw.circle(surface, WHITE, (x, y), GLINT_RADIUS)


def draw_cat_features(surface, p: Player):
    """Draws cat ears and whiskers on the player. These are purely cosmetic and don't affect collision."""
    # Draw cat ears (triangles)
    head_center_x = p.rect.centerx
    head_top_y = p.rect.top

    # Left ear coordinates
    left_ear_points = [
        (head_center_x - EAR_SPACING // 2, head_top_y),  # Bottom right point
        (head_center_x - EAR_SPACING // 2 - EAR_WIDTH, head_top_y),  # Bottom left point
        (
            head_center_x - EAR_SPACING // 2 - EAR_WIDTH // 2,
            head_top_y - EAR_HEIGHT,
        ),  # Top point
    ]

    # Right ear coordinates
    right_ear_points = [
        (head_center_x + EAR_SPACING // 2, head_top_y),  # Bottom left point
        (
            head_center_x + EAR_SPACING // 2 + EAR_WIDTH,
            head_top_y,
        ),  # Bottom right point
        (
            head_center_x + EAR_SPACING // 2 + EAR_WIDTH // 2,
            head_top_y - EAR_HEIGHT,
        ),  # Top point
    ]

    # for both ears, if the player if facing right, move the ears to the left by PADDING, else, move the ears to the right by PADDING
    if p.facing_right:
        left_ear_points = [(x - EAR_PADDING, y) for x, y in left_ear_points]
        right_ear_points = [(x - EAR_PADDING, y) for x, y in right_ear_points]
    else:
        left_ear_points = [(x + EAR_PADDING, y) for x, y in left_ear_points]
        right_ear_points = [(x + EAR_PADDING, y) for x, y in right_ear_points]

    # Draw ears
    pygame.draw.polygon(surface, p.char_color, left_ear_points)
    pygame.draw.polygon(surface, p.char_color, right_ear_points)

    # Draw whiskers (lines)
    whisker_start_x = (
        p.rect.right - WHISKER_OFFSET_X
        if p.facing_right
        else p.rect.left + WHISKER_OFFSET_X
    )
    whisker_start_y = p.rect.top + WHISKER_OFFSET_Y + EYE_RADIUS // 2

    # Direction of whiskers depends on facing direction
    direction = 1 if p.facing_right else -1

    # Draw multiple whisker lines in a fan pattern
    import math

    # Draw middle whisker first (horizontal)
    middle_index = WHISKER_COUNT // 2

    for i in range(WHISKER_COUNT):
        # Calculate angle for each whisker (-WHISKER_ANGLE for top, 0 for middle, WHISKER_ANGLE for bottom)
        angle_degrees = (i - middle_index) * WHISKER_ANGLE
        angle_radians = math.radians(angle_degrees)

        # Calculate end point using trigonometry
        x_offset = direction * WHISKER_LENGTH * math.cos(angle_radians)
        y_offset = WHISKER_LENGTH * math.sin(angle_radians)

        start_pos = (whisker_start_x, whisker_start_y)
        end_pos = (whisker_start_x + x_offset, whisker_start_y + y_offset)

        # Use WHITE color for all whiskers instead of eye_color
        pygame.draw.line(surface, WHITE, start_pos, end_pos, WHISKER_THICKNESS)


def draw_stripes(surface, p: Player):
    """Draws triangular stripes on the player's back for pattern."""
    # Calculate stripe positions on the back of the player
    back_center_x = p.rect.centerx + (-10 if p.facing_right else 10)
    back_start_y = p.rect.top + 15  # Start stripes a bit down from the top
    
    for i in range(STRIPE_COUNT):
        # Calculate vertical position for each stripe
        stripe_y = back_start_y + i * STRIPE_SPACING
        
        # Make sure we don't draw stripes outside the player rectangle
        if stripe_y + STRIPE_HEIGHT > p.rect.bottom:
            break
            
        # Create triangular stripe points pointing toward the front of the cat
        if p.facing_right:
            # Right-facing cat: triangle points right, flat side on the left (back)
            stripe_points = [
                (back_center_x - STRIPE_WIDTH // 2, stripe_y),                    # Back top
                (back_center_x - STRIPE_WIDTH // 2, stripe_y + STRIPE_HEIGHT),    # Back bottom
                (back_center_x + STRIPE_WIDTH // 2, stripe_y + STRIPE_HEIGHT // 2), # Front point
            ]
        else:
            # Left-facing cat: triangle points left, flat side on the right (back)
            stripe_points = [
                (back_center_x + STRIPE_WIDTH // 2, stripe_y),                    # Back top
                (back_center_x + STRIPE_WIDTH // 2, stripe_y + STRIPE_HEIGHT),    # Back bottom
                (back_center_x - STRIPE_WIDTH // 2, stripe_y + STRIPE_HEIGHT // 2), # Front point
            ]
        
        # Draw the triangular stripe
        pygame.draw.polygon(surface, p.stripe_color, stripe_points)


#### TODO: split off damage % and stock lives rendering so that they are rendering last and at the bottom left and right corners of the screen
#### TODO: implement dev info bool flag that, when True, shows all infos, and when False, only shows what should be shown to players normally
def draw_hud(surface, p: Player, label, topright=False):
    """Draws the HUD for a player, showing their state, jumps left, shield HP, lives, and damage percent."""
    fsm = f"FSM: {p.fsm.state.capitalize()}"
    jumps = f"{p.jumps_remaining} jump{'s' if p.jumps_remaining != 1 else ''} left"
    shield = f"Shield HP: {p.shield_hp}"
    shield_attempting = f"Shield Attempting: {'Yes' if p.shield_attempting else 'No'}"
    stocks = f"Lives: {p.lives}"
    percent = f"Damage: {int(p.percent)}%"
    for i, txt in enumerate(
        (label, fsm, jumps, shield, shield_attempting, stocks, percent)
    ):
        surf = font.render(txt, True, WHITE)  # TODO: replace magic vals w/ named vars
        pos = (
            (
                SCREEN_WIDTH - surf.get_width() - HUD_PADDING,
                HUD_PADDING + i * HUD_SPACING,
            )
            if topright
            else (HUD_PADDING, HUD_PADDING + i * HUD_SPACING)
        )
        surface.blit(surf, pos)


def draw_controls(surface, p: Player, label, topright=False):
    """Draws the control scheme for a player below the HUD."""
    # Convert pygame key constants to readable strings
    key_names = {
        pygame.K_a: "A", pygame.K_d: "D", pygame.K_w: "W", pygame.K_s: "S",
        pygame.K_v: "V", pygame.K_c: "C", pygame.K_x: "X",
        pygame.K_LEFT: "left arrow", pygame.K_RIGHT: "right arrow", pygame.K_UP: "up arrow", pygame.K_DOWN: "down arrow",
        pygame.K_SLASH: "/", pygame.K_PERIOD: ".", pygame.K_COMMA: ","
    }
    
    controls = [
        f"{label} Controls:",
        f"Move: {key_names.get(p.controls['left'], '?')}/{key_names.get(p.controls['right'], '?')}",
        f"Jump: {key_names.get(p.controls['up'], '?')}",
        f"Down: {key_names.get(p.controls['down'], '?')}",
        f"Attack: {key_names.get(p.controls['attack'], '?')}",
        f"Shield: {key_names.get(p.controls['shield'], '?')}",
        f"Special: {key_names.get(p.controls['special'], '?')}"
    ]
    
    # Start drawing below the HUD (7 lines of HUD + some spacing)
    start_y = HUD_PADDING + 7 * HUD_SPACING + 20
    
    for i, txt in enumerate(controls):
        surf = font.render(txt, True, WHITE)
        pos = (
            (
                SCREEN_WIDTH - surf.get_width() - HUD_PADDING,
                start_y + i * HUD_SPACING,
            )
            if topright
            else (HUD_PADDING, start_y + i * HUD_SPACING)
        )
        surface.blit(surf, pos)


def draw_player_name(surface, p: Player):
    """Draw the player name above the cat."""
    name_font = pygame.font.SysFont(None, 20)
    
    # Choose color based on player name
    if p.char_name == "P1":
        color = (255, 100, 100)  # Red
    else:
        color = (100, 100, 255)  # Blue
    
    name_text = name_font.render(p.char_name, True, color)
    name_rect = name_text.get_rect(center=(p.rect.centerx, p.rect.top - 25))
    surface.blit(name_text, name_rect)


def reset_game():
    """Reset the game state for a new match"""
    global player1, player2, players, attacks
    
    # Only reset if players exist (they may not exist if coming from character selection)
    if player1 and player2:
        # Reset player 1
        player1.rect.midbottom = (PLAYER1_START_X, PLAYER1_START_Y)
        player1.vel.update(0, 0)
        player1.lives = INITIAL_LIVES
        player1.percent = 0
        player1.shield_hp = SHIELD_MAX_HP
        player1.is_alive = True
        player1.fsm.state = "idle"
        player1.on_ground = False
        player1.jumps_remaining = MAX_JUMPS
        player1.air_dodge_ok = True
        player1.invulnerable = False
        player1.shield_attempting = False
        player1.facing_right = True
        # Reset visual appearance to original color
        player1.reset_visual_state()
        # Reset timers
        player1.respawn_timer = 0
        player1.dodge_timer = 0
        player1.hurt_timer = 0
        player1.stun_timer = 0
        player1.attack_timer = 0
        player1.invulnerable_timer = 0
        player1.done_attacking = True
        # Reset statistics
        player1.attacks_made = 0
        player1.hits_landed = 0
        player1.suicides = 0
        player1.was_hit_before_ko = False
        
        # Reset player 2
        player2.rect.midbottom = (PLAYER2_START_X, PLAYER2_START_Y)
        player2.vel.update(0, 0)
        player2.lives = INITIAL_LIVES
        player2.percent = 0
        player2.shield_hp = SHIELD_MAX_HP
        player2.is_alive = True
        player2.fsm.state = "idle"
        player2.on_ground = False
        player2.jumps_remaining = MAX_JUMPS
        player2.air_dodge_ok = True
        player2.invulnerable = False
        player2.shield_attempting = False
        player2.facing_right = False
        # Reset visual appearance to original color
        player2.reset_visual_state()
        # Reset timers
        player2.respawn_timer = 0
        player2.dodge_timer = 0
        player2.hurt_timer = 0
        player2.stun_timer = 0
        player2.attack_timer = 0
        player2.invulnerable_timer = 0
        player2.done_attacking = True
        # Reset statistics
        player2.attacks_made = 0
        player2.hits_landed = 0
        player2.suicides = 0
        player2.was_hit_before_ko = False
    
    # Clear all attacks
    attacks.empty()


def check_win_condition():
    """Check if either player has won the game"""
    if not player1 or not player2:
        return None, None  # Players not initialized yet
    
    if player1.lives <= 0:
        return player2, player1  # winner, loser
    elif player2.lives <= 0:
        return player1, player2  # winner, loser
    return None, None  # no winner yet


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
        print("Switched to windowed mode")
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
        print(f"Switched to fullscreen mode: {screen_width}x{screen_height}, scale: {scale_factor:.2f}")
        print(f"Using {'integer' if scale_factor == int(scale_factor) else 'fractional'} scaling")


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
                scaled_surface = pygame.transform.scale_by(game_surface, int(scale_factor))
            except AttributeError:
                # Fallback for older pygame versions
                scaled_surface = pygame.transform.scale(game_surface, (scaled_width, scaled_height))
        else:
            # For non-integer scaling, still use regular scale but with size adjustment
            # to maintain crisp pixels as much as possible
            scaled_surface = pygame.transform.scale(game_surface, (scaled_width, scaled_height))
        
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
    
    # Create players with selected characters
    player1 = Player(
        PLAYER1_START_X,
        PLAYER1_START_Y,
        P1_KEYS,
        p1_data['color'],
        eye_color=p1_data['eye_color'],
        char_name="P1",  # Use player ID instead of character name
        facing_right=True,
    )
    
    player2 = Player(
        PLAYER2_START_X,
        PLAYER2_START_Y,
        P2_KEYS,
        p2_data['color'],
        eye_color=p2_data['eye_color'],
        char_name="P2",  # Use player ID instead of character name
        facing_right=False,
    )
    
    # Update stripe colors based on character selection
    player1.stripe_color = p1_data['stripe_color']
    player2.stripe_color = p2_data['stripe_color']
    
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
        fs_text = "F11: Toggle Fullscreen" + (" | ESC: Exit Fullscreen" if is_fullscreen else "")
        fs_surf = font.render(fs_text, True, WHITE)
        get_render_surface().blit(
            fs_surf,
            (
                SCREEN_WIDTH - fs_surf.get_width() - HUD_PADDING,
                SCREEN_HEIGHT - HUD_SPACING,
            ),
        )
        
        # Draw back to menu instruction
        back_text = "Hold B for 1 second to return to main menu"
        back_surf = font.render(back_text, True, WHITE)
        get_render_surface().blit(
            back_surf,
            (
                HUD_PADDING,
                SCREEN_HEIGHT - HUD_SPACING,
            ),
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
        for pl in platforms:
            render_surface.blit(pl.image, pl.rect)

        # Draw alive players
        for p in players:
            if (
                not p.is_alive
            ):  # TODO: replace this w/ KO state check after implementing KO state
                continue
            # Draw tail first (behind player)
            p.tail.draw(render_surface)
            # Draw player body
            render_surface.blit(p.image, p.rect)
            # Draw stripes on the player's back
            draw_stripes(render_surface, p)
            draw_eye(render_surface, p)
            draw_eye(render_surface, p, eye=False)  # Draw a glint in the eye
            draw_cat_features(render_surface, p)  # Draw cat features (ears and whiskers)
            draw_stripes(render_surface, p)  # Draw stripes on the player's back
            # Draw player name above cat
            draw_player_name(render_surface, p)
            if p.fsm.state == "shield":
                #### TODO: convert shield radius magic nums to config constants (READY)
                ratio = p.shield_hp / SHIELD_MAX_HP
                shield_radius = int(MAX_SHIELD_RADIUS * ratio)
                r = max(MIN_SHIELD_RADIUS, shield_radius)
                s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                # s = surface, r = radius, (r,r) is for centering the circle on the player character
                pygame.draw.circle(
                    s, (*SHIELD_COLOR, 100), (r, r), r
                )  # *SHIELD_COLOR is a tuple unpacking technique to get the RGB values, 100 is the alpha value for transparency
                # Draw shield bubble centered on player
                render_surface.blit(s, (p.rect.centerx - r, p.rect.centery - r))

        for a in attacks:
            render_surface.blit(a.image, a.rect)

        # Draw HUD only if players exist
        if player1 and player2:
            draw_hud(render_surface, player1, "P1")  # drawn by default in upper-left corner
            draw_hud(render_surface, player2, "P2", topright=True)

            # Draw player controls below the HUD
            draw_controls(render_surface, player1, "P1")  # drawn by default below P1 HUD
            draw_controls(render_surface, player2, "P2", topright=True)  # drawn below P2 HUD

        # draw keys pressed for debugging
        if frame_input:
            # keys = ", ".join(
            #     f"{k}: {v}" for k, v in frame_input.items() if v
            # )
            keys_surf = font.render(frame_input.__str__(), True, WHITE)
            render_surface.blit(keys_surf, (HUD_PADDING, SCREEN_HEIGHT - HUD_SPACING))
        # draw FPS and fullscreen instructions
        fps_surf = font.render(f"FPS: {clock.get_fps():.2f}", True, WHITE)
        render_surface.blit(
            fps_surf,
            (
                SCREEN_WIDTH - fps_surf.get_width() - HUD_PADDING,
                SCREEN_HEIGHT - HUD_SPACING,
            ),
        )
        
        # Draw fullscreen instructions
        fs_text = "F11: Toggle Fullscreen" + (" | ESC: Exit Fullscreen" if is_fullscreen else "")
        fs_surf = font.render(fs_text, True, WHITE)
        render_surface.blit(
            fs_surf,
            (
                SCREEN_WIDTH - fs_surf.get_width() - HUD_PADDING,
                SCREEN_HEIGHT - HUD_SPACING * 2,
            ),
        )
    
    elif current_state == "win_screen":
        # Render win screen
        screen_manager.render(get_render_surface())

    present_frame()

pygame.quit()
sys.exit()
