"""
Purpose: Central configuration module.

Contents:
- Screen dimensions (WIDTH, HEIGHT), framerate (FPS)
- Physics constants (gravity, fall speed, movement speed)
- Player action constants (jump velocity, dodge frames, max jumps)
- UI constants (attack hit-box size and lifetime, eye offset, shield color)

Use: Shared constants across modules for tuning gameplay and UI.
"""

WIDTH, HEIGHT = 960, 540
FPS = 60

GRAVITY        = 0.5
MAX_FALL_SPEED = 12
MOVE_SPEED     = 5
JUMP_VEL       = -10
DODGE_FRAMES   = 15
MAX_JUMPS      = 2     # single + double

ATTACK_LIFETIME = 12
ATTACK_SIZE     = (30, 18)

EYE_OFFSET_X = 10
EYE_OFFSET_Y = 12
EYE_RADIUS   = 10

BG_COLOR      = (60, 60, 70)
SHIELD_COLOR  = (80, 180, 255)
