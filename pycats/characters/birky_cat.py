"""FighterData for "Birky" — the Kirby archetype (floaty featherweight). Slice 1 of #228.

Birky is the **first** fighter to diverge on the per-fighter MOVEMENT SCALARS. Values
from the #229 scoping spike (PM Kirby, proportional-to-Mario; pin/playtest later):

    weight 70 · gravity 0.42 · max_fall_speed 12 · move_speed 5 · max_jumps 6 · jump_vel -11

Per #120, these scalars are entered RAW (the ×5.4 unit scale is for *spatial* values,
not needed this slice).

Placeholders reused from the default cat (slice 1 = scalars only):
  - `hurtbox`, `moves`, crouch/prone geometry — Birky's real moves are **slice 2**;
  - per-fighter body size is **not** a `FighterData` field (the rendered `stand_size`
    is the global `config.PLAYER_SIZE`), so a smaller round body is out of scope here.

Caveat (#229): pycats has a single `move_speed` knob (ground == air), so Kirby's
slow-walk / fast-air split can't be captured — `move_speed` leans to the
slow-featherweight identity. The genuine `fast-fall` mechanic is a separate, shared
engine ticket; selectability (making Birky human-pickable) is gated on #117/#127.
"""
from pycats.characters.default_cat import DEFAULT_FIGHTER_DATA as _DEFAULT
from pycats.combat.data import Circle, FighterData, Hitbox, MoveData

# --- Jab (slice 2, #240): PM3.6 Kirby jab 1 (Attack11) ------------------------
# rukaidata PM3.6 Kirby Attack11: 16 frames total (IASA 16), hitbox active ~frame 3,
# damage 3.0, angle 361 (Sakurai sentinel), BKB 8, KBG 50 (normal knockback, not
# WDSK). #120 units: frames/%/angle/BKB/KBG RAW; radius 3.13u × 5.4 ≈ 17 px. Active
# widened to 2f (rukaidata is 1f on f3) for pycats hit detection — playtest. dx/dy
# approximated by the short-reach convention (featherweight: closer than the default
# attack's dx=46), per the nalio_cat.py precedent (bone-relative offsets not mapped).
_BIRKY_JAB = MoveData(
    name="jab",
    in_air=False,
    startup=2,
    active=2,
    recovery=12,  # 2 + 2 + 12 = 16 (PM3.6 total / IASA)
    hitboxes=(
        Hitbox(circle=Circle(dx=38, dy=27, r=17), damage=3.0, angle=361,
               base_knockback=8.0, knockback_growth=50.0),
        Hitbox(circle=Circle(dx=30, dy=28, r=17), damage=3.0, angle=361,
               base_knockback=8.0, knockback_growth=50.0),
    ),
)

# --- Down-tilt, mapped to the "attack" slot (slice 2, #245): PM3.6 Kirby AttackLw3 -
# rukaidata PM3.6 Kirby AttackLw3: 30f total, IASA 21, active 4-7; four hitboxes
# (skip the r=0 one), all damage 10, angle 20, BKB 40, KBG 30. #120 units: scalars
# RAW; radii round(size×5.4) for 3.91/4.69/3.55u ≈ 21/25/19. A low poke → high dy
# (near the feet); dx short (featherweight). dx/dy approximated by convention
# (bone-relative offsets not mapped), flagged for playtest — per nalio_cat.py.
_BIRKY_DTILT = MoveData(
    name="dtilt",
    in_air=False,
    startup=3,
    active=4,
    recovery=14,  # active f4-7; 3 + 4 + 14 = 21 (PM3.6 IASA)
    hitboxes=(
        Hitbox(circle=Circle(dx=42, dy=48, r=25), damage=10.0, angle=20,
               base_knockback=40.0, knockback_growth=30.0),
        Hitbox(circle=Circle(dx=34, dy=49, r=21), damage=10.0, angle=20,
               base_knockback=40.0, knockback_growth=30.0),
        Hitbox(circle=Circle(dx=28, dy=50, r=19), damage=10.0, angle=20,
               base_knockback=40.0, knockback_growth=30.0),
    ),
)

BIRKY_FIGHTER_DATA = FighterData(
    # hurtbox/posture still reuse the default cat (body geometry is a separate concern);
    # both moves are now Birky's own — d-tilt in the "attack" slot (#245) + jab (#240).
    hurtbox=_DEFAULT.hurtbox,
    moves={"attack": _BIRKY_DTILT, "jab": _BIRKY_JAB},
    crouch_size=_DEFAULT.crouch_size,
    crouch_hurtbox=_DEFAULT.crouch_hurtbox,
    prone_size=_DEFAULT.prone_size,
    prone_hurtbox=_DEFAULT.prone_hurtbox,
    # the featherweight movement scalars (#229)
    weight=70,
    gravity=0.42,
    max_fall_speed=12,
    move_speed=5,
    max_jumps=6,
    jump_vel=-11,
)
