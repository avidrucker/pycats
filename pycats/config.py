"""
Purpose: Central configuration module.

Contents:
- Screen dimensions (SCREEN_WIDTH, SCREEN_HEIGHT), framerate (FPS)
- Physics constants (gravity, fall speed, movement speed)
- Player action constants (jump velocity, dodge frames, max jumps)
- UI constants (attack hit-box size and lifetime, eye offset, shield color)

Use: Shared constants across modules for tuning gameplay and UI.
"""

#### TODO: implement unique attacks for each player
#### TODO: implement attack cooldowns
#### TODO: implement attack blocking via having enough shield strength left
#### TODO: implement attack dodging
#### TODO: implement character selection that offers heavy, medium, & light-weight choices where heavy characters do more damage but are slower, and lighter characters are faster but deal less damage
#### TODO: implement knockback based on attack strength and player weight
#### TODO: implement attack combos that can be chained together for more damage
#### TODO: implement attack hit-stun that prevents the player from moving for a short time after being hit
#### TODO: implement player weight attribute that affects knockback

SCREEN_WIDTH, SCREEN_HEIGHT = 960, 540
FPS = 60

GRAVITY = 0.5
MAX_FALL_SPEED = 13
MOVE_SPEED = 6
JUMP_VEL = -13
DODGE_FRAMES = 15
MAX_JUMPS = 2  # single + double

# ---------------- physics constants --------------
GROUND_FRICTION = 0.5  # 1.0 = ice; 0.0 = instant stop
AIR_FRICTION    = 0.85

# Timers (frames)
HURT_TIME = 12
STUN_TIME = 60
DODGE_TIME = 14
DODGE_SPEED = 22  # horizontal boost for a roll

# ---------------- combat / attacks ----------------
#### TODO: implement variable attack lifetimes, attack sizes, attack colors, and hit damage, save each attack into a dictionary with the attack name as the key
ATTACK_LIFETIME = 12
PLAYER_ATTACK_DURATION = 12  # this can be different than the lifetime of an attack, for example, a fireball could take 6 frames to fire, and then the lifetime of the fireball could be as long as 120 frames
ATTACK_SIZE = (30, 18)  # width, height
HIT_DAMAGE = 10  # default damage per hit

# ---------------- shield / bubble ---------------
SHIELD_MAX_HP = 50  # fresh shield bubble hit points
MAX_SHIELD_RADIUS = 40
MIN_SHIELD_RADIUS = 10

# ---------------- knockback ----------------
KNOCKBACK_SCALE = 0.5
KNOCKBACK_BASE = 5

# ---------------- platform constants ------------
# note: 300 is good for a 540 width map
THICK_PLAT_WIDTH = 800
# note: 40 is good for a 540 height map
THICK_PLAT_HEIGHT = 80
THICK_PLAT_Y_OFF = THICK_PLAT_HEIGHT
THIN_PLAT_WIDTH = 150
THIN_PLAT_HEIGHT = 20
THIN_PLAT_LEFT_X_OFF = -200
THIN_PLAT_RIGHT_X_OFF = 200
THIN_PLAT_Y_OFF = 200
GLOBAL_Y_OFF = 50

THICK_PLAT_DICT = {
    "x": SCREEN_WIDTH // 2 - THICK_PLAT_WIDTH // 2,
    "y": SCREEN_HEIGHT - THICK_PLAT_Y_OFF - GLOBAL_Y_OFF,
    "w": THICK_PLAT_WIDTH,
    "h": THICK_PLAT_HEIGHT,
}

THIN_PLAT_DICT_L = {
    "x": SCREEN_WIDTH // 2 - THIN_PLAT_WIDTH // 2 + THIN_PLAT_LEFT_X_OFF,
    "y": SCREEN_HEIGHT - THIN_PLAT_Y_OFF - GLOBAL_Y_OFF,
    "w": THIN_PLAT_WIDTH,
    "h": THIN_PLAT_HEIGHT,
}

THIN_PLAT_DICT_R = {
    "x": SCREEN_WIDTH // 2 - THIN_PLAT_WIDTH // 2 + THIN_PLAT_RIGHT_X_OFF,
    "y": SCREEN_HEIGHT - THIN_PLAT_Y_OFF - GLOBAL_Y_OFF,
    "w": THIN_PLAT_WIDTH,
    "h": THIN_PLAT_HEIGHT,
}

# ---------------- player size, position, color ---------------
PLAYER_SIZE = (40, 60)  # width, height
PLAYER1_START_X = SCREEN_WIDTH // 2 + THIN_PLAT_LEFT_X_OFF
PLAYER2_START_X = SCREEN_WIDTH // 2 + THIN_PLAT_RIGHT_X_OFF
PLAYER1_START_Y = SCREEN_HEIGHT - PLAYER_SIZE[1] - GLOBAL_Y_OFF - THIN_PLAT_Y_OFF
PLAYER2_START_Y = SCREEN_HEIGHT - PLAYER_SIZE[1] - GLOBAL_Y_OFF - THIN_PLAT_Y_OFF

EYE_OFFSET_X = 10
EYE_OFFSET_Y = 12
EYE_RADIUS = 10

# ---------------- Other UI / visuals --------------------
HUD_PADDING = 10
HUD_SPACING = 22

# ---------------- colors -------------------
BG_COLOR = (60, 60, 70)
P1_COLOR = (255, 160, 64)  # orange
P2_COLOR = (90, 90, 90)  # gray
BLACK = (0, 0, 0)  # black
WHITE = (255, 255, 255)  # white
RED = (255, 0, 0)  # red
YELLOW = (255, 255, 0)  # yellow

# ---------------- cat features -----------------
EAR_WIDTH = 15
EAR_HEIGHT = 20
EAR_SPACING = -2
EAR_PADDING = 5
WHISKER_OFFSET_Y = 20
WHISKER_OFFSET_X = 10
WHISKER_LENGTH = 20
WHISKER_THICKNESS = 2
WHISKER_SPACING = 4
WHISKER_COUNT = 3
WHISKER_ANGLE = 25  # Angle in degrees between whiskers

# ---------------- tail features -----------------
TAIL_SEGMENTS = 30  # Number of segments in the tail
TAIL_SEGMENT_LENGTH = 3  # Length of each segment
TAIL_SEGMENT_WIDTH = 15  # Width of each segment (tapers towards the tip)
TAIL_BASE_OFFSET_X = 15  # Horizontal offset from player center to tail base
TAIL_BASE_OFFSET_Y = 5  # Vertical offset from player bottom to tail base
TAIL_WAVE_AMPLITUDE = 0.25  # Amplitude of the idle wave motion (radians)
TAIL_WAVE_FREQUENCY = 0.05  # Much slower frequency for more graceful idle motion
TAIL_FOLLOW_STRENGTH = 0.05  # Much lower for slower following
TAIL_DAMPING = 0.92  # Higher damping for smoother motion
TAIL_UPDATE_FREQUENCY = 1  # Update every frame for smoother motion
TAIL_MIN_MOVEMENT_THRESHOLD = 0.05  # Lower threshold for more responsive small movements
TAPER_MODIFER = 0.1  # Tapering effect for tail segments

# New drag/trail constants for more graceful movement
TAIL_DRAG_STRENGTH = 0.9      # Higher drag for more trailing effect
TAIL_GRAVITY_EFFECT = 0.7     # Moderate gravity effect
TAIL_MOMENTUM_DECAY = 0.95    # Higher momentum retention for flowing motion
TAIL_MAX_BEND_ANGLE = 0.7     # Smaller max bend for more natural curves
TAIL_VELOCITY_SENSITIVITY = 0.1  # Much lower sensitivity for gentler response

#### TODO: implement player color (yellow, blue, red, green) which will affect the shield color
#### TODO: implement parameterized shield color
SHIELD_COLOR = (80, 180, 255)

# ---------------- stocks / blast zone --------
INITIAL_LIVES = 3
BLAST_PADDING = 50  # px beyond screen = KO
RESPAWN_DELAY_FRAMES = int(2 * FPS)  # 2 s freeze before respawn
