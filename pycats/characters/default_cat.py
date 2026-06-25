"""
pycats/characters/default_cat.py

Purpose: Default FighterData shared by all CAT_CHARACTERS in Phase 0.

Contains:
- DEFAULT_FIGHTER_DATA: FighterData with a 2-circle hurtbox and one ground
  attack move approximating today's basic attack.

Hurtbox design (PLAYER_SIZE = 40 wide, 60 tall):
  The fighter origin is the top-left corner of the player rect.
  Center of the rect: (20, 30).
  We split the body into upper and lower halves with two circles:

    Upper circle: dx=20, dy=15  (upper third of body, y=0..30)
                  r=14  (just under half the width = 20; 14 keeps it inside)
    Lower circle: dx=20, dy=45  (lower two-thirds, y=30..60)
                  r=14

  Together these two circles cover the full 40x60 body reasonably well,
  with modest overlap in the middle. Radius 14 fits inside a 40-wide rect
  (max would be 20) while giving good coverage.

  Note: dx=20 centres each circle horizontally within the 40-wide body.

Attack move ("attack") — ground attack approximating the current basic attack.
  This move's data IS the single source of truth (the old global ATTACK_LIFETIME
  / HIT_DAMAGE fallbacks were retired in #70). The values below derive from the
  former config constants for continuity:
    total window = 12  (was PLAYER_ATTACK_DURATION; still in config)
    active/lifetime = 3 active frames (was the global ATTACK_LIFETIME=12)
    damage = 10        (was the global HIT_DAMAGE)
  Note: ATTACK_SIZE=(30,18) survives as a render-only constant (the drawn rect).

  The drawn rect is 30×18, centered on the hitbox circle below.

  Phase 0 timing split for 12-frame total:
    startup  = 3  (wind-up; short — it's a quick jab)
    active   = 3  (hitbox window; brief)
    recovery = 6  (cool-down; double the active time)
    total    = 12  ✓

  Hitbox circle:
    dx = 27  — offset rightward: body is 40 px wide, center at x=20; going
               27 px right of origin places the circle center 7 px past the
               right edge of the body, matching the spawned rect position.
    dy = 30  — vertically centred on the body (height=60, centre=30)
    r  = 12  — approximates the 30×18 rect; short dimension is 9 px, long
               is 15 px; radius 12 is a reasonable circle approximation.

  damage = 10.0  (the jab's damage; formerly the global HIT_DAMAGE)
  angle  = 0     (horizontal launch; matches current behaviour)
"""

from pycats.combat.data import Circle, FighterData, Hitbox, Hurtbox, MoveData

# --- Hurtbox: 2-circle vertical stack covering the 40×60 player body -------
# Origin = top-left of player rect; dx=20 centres circles horizontally.
_HURTBOX = Hurtbox(
    circles=(
        Circle(dx=20, dy=15, r=14),   # upper body (head/torso region)
        Circle(dx=20, dy=45, r=14),   # lower body (legs region)
    )
)

# --- Ground attack move -----------------------------------------------------
_ATTACK_HITBOX = Hitbox(
    circle=Circle(dx=27, dy=30, r=12),
    damage=10.0,
    angle=0,
    base_knockback=30.0,    # ⚠ initial tuning — a light jab; playtest with KNOCKBACK_LAUNCH_FACTOR/DECAY
    knockback_growth=100.0,
)

_ATTACK_MOVE = MoveData(
    name="attack",
    in_air=False,
    startup=3,
    active=3,
    recovery=6,
    hitboxes=(_ATTACK_HITBOX,),
)

# --- Assembled FighterData ---------------------------------------------------
DEFAULT_FIGHTER_DATA = FighterData(
    hurtbox=_HURTBOX,
    moves={"attack": _ATTACK_MOVE},
)
