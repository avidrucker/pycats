"""
Purpose: Central configuration module.

Contents:
- Screen dimensions (SCREEN_WIDTH, SCREEN_HEIGHT), framerate (FPS)
- Physics constants (gravity, fall speed, movement speed)
- Player action constants (jump velocity, dodge frames, max jumps)
- UI constants (attack hit-box size and lifetime, eye offset, shield color)

Use: Shared constants across modules for tuning gameplay and UI.
"""

#### TODO: create global constants to move entire map up/down/left/right
#### TODO: implement unique attacks for each player
#### TODO: implement attack cooldowns
#### TODO: implement attack blocking
#### TODO: implement attack dodging
#### TODO: implement character selection that offers heavy, medium, & light-weight choices where heavy characters do more damage but are slower, and lighter characters are faster but deal less damage
#### TODO: implement knockback based on attack strength and player weight
#### TODO: implement attack combos that can be chained together for more damage
#### TODO: implement attack hit-stun that prevents the player from moving for a short time after being hit
#### TODO: implement player weight attribute that affects knockback

SCREEN_WIDTH, SCREEN_HEIGHT = 960, 540
FPS = 60

GRAVITY        = 0.5
MAX_FALL_SPEED = 12
MOVE_SPEED     = 5
JUMP_VEL       = -10
DODGE_FRAMES   = 15
MAX_JUMPS      = 2     # single + double

# ---------------- combat / attacks ----------------
ATTACK_LIFETIME = 12
ATTACK_SIZE     = (30, 18)

# ---------------- platform constants ------------
# note: 300 is good for a 540 width map
THICK_PLAT_WIDTH = 800
# note: 40 is good for a 540 height map 
THICK_PLAT_HEIGHT = 80
THICK_PLAT_Y_OFF = THICK_PLAT_HEIGHT
THIN_PLAT_WIDTH  = 150
THIN_PLAT_HEIGHT  = 20
THIN_PLAT_LEFT_X_OFF  = -200
THIN_PLAT_RIGHT_X_OFF = 200
THIN_PLAT_Y_OFF = 175
GLOBAL_Y_OFF = 50

THICK_PLAT_DICT = {
    "x": SCREEN_WIDTH//2-THICK_PLAT_WIDTH//2,
    "y": SCREEN_HEIGHT-THICK_PLAT_Y_OFF-GLOBAL_Y_OFF,
    "w": THICK_PLAT_WIDTH,
    "h": THICK_PLAT_HEIGHT,
}

THIN_PLAT_DICT_L = {
    "x": SCREEN_WIDTH//2-THIN_PLAT_WIDTH//2+THIN_PLAT_LEFT_X_OFF, "y": SCREEN_HEIGHT-THIN_PLAT_Y_OFF-GLOBAL_Y_OFF, 
    "w": THIN_PLAT_WIDTH, 
    "h": THIN_PLAT_HEIGHT
}

THIN_PLAT_DICT_R = {
    "x": SCREEN_WIDTH//2-THIN_PLAT_WIDTH//2+THIN_PLAT_RIGHT_X_OFF, "y": SCREEN_HEIGHT-THIN_PLAT_Y_OFF-GLOBAL_Y_OFF, 
    "w": THIN_PLAT_WIDTH, 
    "h": THIN_PLAT_HEIGHT
}

# ---------------- player size, position, color ---------------
PLAYER_SIZE = (40, 60) # width, height
PLAYER1_START_X = SCREEN_WIDTH//2 + THIN_PLAT_LEFT_X_OFF
PLAYER2_START_X = SCREEN_WIDTH//2 + THIN_PLAT_RIGHT_X_OFF
PLAYER1_START_Y = SCREEN_HEIGHT - PLAYER_SIZE[1] - GLOBAL_Y_OFF - THIN_PLAT_Y_OFF
PLAYER2_START_Y = SCREEN_HEIGHT - PLAYER_SIZE[1] - GLOBAL_Y_OFF - THIN_PLAT_Y_OFF

EYE_OFFSET_X = 10
EYE_OFFSET_Y = 12
EYE_RADIUS   = 10

P1_COLOR = (255, 160, 64)  # orange
P2_COLOR = (90, 90, 90)     # gray
BLACK    = (0, 0, 0)        # black
WHITE    = (255, 255, 255)  # white

# ---------------- Other UI / visuals --------------------
BG_COLOR      = (60, 60, 70)
SHIELD_COLOR  = (80, 180, 255)
MAX_SHIELD_RADIUS = 30
HUD_PADDING = 10
HUD_SPACING = 22

# ---------------- stocks / blast zone --------
INITIAL_LIVES       = 3
BLAST_PADDING       = 50                         # px beyond screen = KO
RESPAWN_DELAY_FRAMES = int(2 * FPS)              # 2 s freeze before respawn

#### TODO: implement spawn points for each player with corresponding constants
