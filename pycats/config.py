"""
Purpose: Central configuration module.

Contents:
- Screen dimensions (WIDTH, HEIGHT), framerate (FPS)
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

#### TODO: rename width/height to screen_width/screen_height for clarity
WIDTH, HEIGHT = 960, 540
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

# ---------------- UI / visuals --------------------
EYE_OFFSET_X = 10
EYE_OFFSET_Y = 12
EYE_RADIUS   = 10

BG_COLOR      = (60, 60, 70)
SHIELD_COLOR  = (80, 180, 255)
MAX_SHIELD_RADIUS = 30

# ---------------- stocks / blast zone --------
INITIAL_LIVES       = 3
BLAST_PADDING       = 50                         # px beyond screen = KO
RESPAWN_DELAY_FRAMES = int(2 * FPS)              # 2 s freeze before respawn

#### TODO: implement spawn points for each player with corresponding constants
