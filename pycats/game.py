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
    EAR_WIDTH, EAR_HEIGHT, EAR_SPACING, EAR_PADDING, WHISKER_LENGTH, 
    WHISKER_THICKNESS, WHISKER_SPACING, WHISKER_COUNT, WHISKER_ANGLE,
    TAIL_SEGMENTS, TAIL_SEGMENT_LENGTH, TAIL_SEGMENT_WIDTH
)
from .entities import Platform, Player
from .systems import combat
from .core import input as inp
from .core.physics import resolve_player_push

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

#### TODO: convert player start positions to config constants (READY)
player1 = Player(
    PLAYER1_START_X,
    PLAYER1_START_Y,
    P1_KEYS,
    P1_COLOR,
    eye_color=BLACK,
    char_name="Player 1",
    facing_right=True,
)
player2 = Player(
    PLAYER2_START_X,
    PLAYER2_START_Y,
    P2_KEYS,
    P2_COLOR,
    eye_color=WHITE,
    char_name="Player 2",
    facing_right=False,
)
players = pygame.sprite.Group(player1, player2)
attacks = pygame.sprite.Group()

# ------------------------------------------------ pygame set-up
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 24)


# ------------------------------------------------ helpers
def draw_eye(p: Player):
    x = p.rect.right - EYE_OFFSET_X if p.facing_right else p.rect.left + EYE_OFFSET_X
    y = p.rect.top + EYE_OFFSET_Y
    pygame.draw.circle(screen, p.eye_color, (x, y), EYE_RADIUS)


def draw_cat_features(p: Player):
    """Draws cat ears and whiskers on the player. These are purely cosmetic and don't affect collision."""
    # Draw cat ears (triangles)
    head_center_x = p.rect.centerx
    head_top_y = p.rect.top

    # Left ear coordinates
    left_ear_points = [
        (head_center_x - EAR_SPACING // 2, head_top_y),  # Bottom right point
        (head_center_x - EAR_SPACING // 2 - EAR_WIDTH, head_top_y),  # Bottom left point
        (head_center_x - EAR_SPACING // 2 - EAR_WIDTH // 2, head_top_y - EAR_HEIGHT),  # Top point
    ]

    # Right ear coordinates
    right_ear_points = [
        (head_center_x + EAR_SPACING // 2, head_top_y),  # Bottom left point
        (head_center_x + EAR_SPACING // 2 + EAR_WIDTH, head_top_y),  # Bottom right point
        (head_center_x + EAR_SPACING // 2 + EAR_WIDTH // 2, head_top_y - EAR_HEIGHT),  # Top point
    ]

    # for both ears, if the player if facing right, move the ears to the left by PADDING, else, move the ears to the right by PADDING
    if p.facing_right:
        left_ear_points = [(x - EAR_PADDING, y) for x, y in left_ear_points]
        right_ear_points = [(x - EAR_PADDING, y) for x, y in right_ear_points]
    else:
        left_ear_points = [(x + EAR_PADDING, y) for x, y in left_ear_points]
        right_ear_points = [(x + EAR_PADDING, y) for x, y in right_ear_points]

    # Draw ears
    pygame.draw.polygon(screen, p.char_color, left_ear_points)
    pygame.draw.polygon(screen, p.char_color, right_ear_points)

    # Draw whiskers (lines)
    whisker_start_x = p.rect.right - EYE_OFFSET_X if p.facing_right else p.rect.left + EYE_OFFSET_X
    whisker_start_y = p.rect.top + EYE_OFFSET_Y + EYE_RADIUS // 2

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
        pygame.draw.line(screen, WHITE, start_pos, end_pos, WHISKER_THICKNESS)


#### TODO: split off damage % and stock lives rendering so that they are rendering last and at the bottom left and right corners of the screen
#### TODO: implement dev info bool flag that, when True, shows all infos, and when False, only shows what should be shown to players normally
def draw_hud(p: Player, label, topright=False):
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
        screen.blit(surf, pos)


# ------------------------------------------------ main loop
running = True
while running:
    dt = clock.tick(FPS)
    frame_input, events = inp.poll()
    for ev in events:
        if ev.type == pygame.QUIT:
            running = False

    # ---- update
    for p in players:
        p.update(frame_input, platforms, attacks)
    resolve_player_push(list(players))
    attacks.update()
    combat.process_hits(players, attacks)

    # ---- render
    screen.fill(BG_COLOR)
    for pl in platforms:
        screen.blit(pl.image, pl.rect)

    # Draw alive players
    for p in players:
        if (
            not p.is_alive
        ):  # TODO: replace this w/ KO state check after implementing KO state
            continue
        # Draw tail first (behind player)
        p.tail.draw(screen)
        # Draw player body
        screen.blit(p.image, p.rect)
        draw_eye(p)
        draw_cat_features(p)  # Draw cat features (ears and whiskers)
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
            screen.blit(s, (p.rect.centerx - r, p.rect.centery - r))

    for a in attacks:
        screen.blit(a.image, a.rect)

    draw_hud(player1, "P1")  # drawn by default in upper-left corner
    draw_hud(player2, "P2", topright=True)

    # draw keys pressed for debugging
    if frame_input:
        # keys = ", ".join(
        #     f"{k}: {v}" for k, v in frame_input.items() if v
        # )
        keys_surf = font.render(frame_input.__str__(), True, WHITE)
        screen.blit(keys_surf, (HUD_PADDING, SCREEN_HEIGHT - HUD_SPACING))
    # draw FPS
    fps_surf = font.render(f"FPS: {clock.get_fps():.2f}", True, WHITE)
    screen.blit(
        fps_surf,
        (
            SCREEN_WIDTH - fps_surf.get_width() - HUD_PADDING,
            SCREEN_HEIGHT - HUD_SPACING,
        ),
    )

    pygame.display.flip()

pygame.quit()
sys.exit()
