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

  Hitbox circle (reach convention — see the inline note on _ATTACK_HITBOX):
    dx = 46  — offset rightward from the body's left edge; 26 px right of the
               body centre (x=20), reaching ~18 px past the 40 px body so the
               jab connects an opponent's body-centre hurtbox when flush and
               across the bot's engagement range. Mirrors around the body centre
               when facing left (see geometry.resolve_circle, #64).
    dy = 30  — vertically centred on the body (height=60, centre=30)
    r  = 12  — circle radius (the drawn rect is the render-only ATTACK_SIZE).

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
    # Reach convention (#64): dx is the hitbox centre offset from the body's
    # left edge (body is 40 wide; centre at 20). For the jab to connect an
    # opponent's body-centre hurtbox across the bot's engagement range (centre
    # gap ~12–45) AND when flush (settled push gap ~41), the hitbox centre must
    # land within sqrt((r+14)^2 - 15^2) ≈ 21 px of the opponent's body centre.
    # dx=46 (26 px right of centre, r=12 → reaches ~18 px past the 40-wide body)
    # sits the hitbox in that window. Playtest starting point.
    circle=Circle(dx=46, dy=30, r=12),
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

# --- Crouch geometry (#124) --------------------------------------------------
# The default cat crouches too (so the playable cosmetic cats can crouch in the
# live game). 40×60 stand box → squarish 40×40 crouch box, feet planted, with a
# lower/shorter hurtbox. Golden-safe: the headless replay never presses down.
_CROUCH_SIZE = (40, 40)
_CROUCH_HURTBOX = Hurtbox(
    circles=(
        Circle(dx=20, dy=20, r=14),
        Circle(dx=20, dy=32, r=12),
    )
)

# --- Assembled FighterData ---------------------------------------------------
DEFAULT_FIGHTER_DATA = FighterData(
    hurtbox=_HURTBOX,
    moves={"attack": _ATTACK_MOVE},
    crouch_size=_CROUCH_SIZE,
    crouch_hurtbox=_CROUCH_HURTBOX,
)
