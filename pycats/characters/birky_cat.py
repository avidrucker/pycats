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

# --- Forward-tilt (slice 2, #247): PM3.6 Kirby AttackS3S -----------------------
# rukaidata PM3.6 Kirby AttackS3S: 33f total, IASA 28, active 5-8; three hitboxes,
# all damage 11, angle 361 (Sakurai), BKB 8, KBG 100 (no WDSK). #120 units: scalars
# RAW; radii round(size×5.4) for 3.52/3.91/3.75u ≈ 19/21/20. A forward poke → dx
# increasing (offsets 0/3.95/7.7u), mid-height dy. Approximated/playtest per precedent.
_BIRKY_FTILT = MoveData(
    name="ftilt",
    in_air=False,
    startup=4,
    active=4,
    recovery=20,  # active f5-8; 4 + 4 + 20 = 28 (PM3.6 IASA)
    hitboxes=(
        Hitbox(circle=Circle(dx=38, dy=34, r=19), damage=11.0, angle=361,
               base_knockback=8.0, knockback_growth=100.0),
        Hitbox(circle=Circle(dx=46, dy=33, r=21), damage=11.0, angle=361,
               base_knockback=8.0, knockback_growth=100.0),
        Hitbox(circle=Circle(dx=52, dy=33, r=20), damage=11.0, angle=361,
               base_knockback=8.0, knockback_growth=100.0),
    ),
)

# --- Up-tilt (slice 2, #249): PM3.6 Kirby AttackHi3 — a two-window upward poke -----
# rukaidata PM3.6 Kirby AttackHi3: 24f total, IASA 24, active 4-10. Two windows
# (per-hitbox active_start/active_end, like nalio_cat.py u-air): early f4-5 (dmg 8,
# angle 92), late f6-10 (dmg 6, angle 88); both BKB 40, KBG 118/114; sizes 4.69/5.47u
# → radii ≈ 25/30 (×5.4). Hits above the cat (low dy, near/over the head), centred dx.
# Approximated/playtest per precedent. #120 units: scalars RAW, radius ×5.4.
def _utilt_box(dx, dy, r, damage, angle, kbg, start, end):
    return Hitbox(circle=Circle(dx=dx, dy=dy, r=r), damage=damage, angle=angle,
                  base_knockback=40.0, knockback_growth=kbg,
                  active_start=start, active_end=end)


_BIRKY_UTILT = MoveData(
    name="utilt",
    in_air=False,
    startup=3,
    active=7,
    recovery=14,  # active f4-10; 3 + 7 + 14 = 24 (PM3.6 IASA)
    hitboxes=(
        _utilt_box(dx=22, dy=8, r=25, damage=8.0, angle=92, kbg=118.0, start=4, end=5),
        _utilt_box(dx=30, dy=10, r=30, damage=8.0, angle=92, kbg=114.0, start=4, end=5),
        _utilt_box(dx=22, dy=8, r=25, damage=6.0, angle=88, kbg=118.0, start=6, end=10),
        _utilt_box(dx=30, dy=10, r=30, damage=6.0, angle=88, kbg=114.0, start=6, end=10),
    ),
)

# --- Neutral-air (slice 3, #255): PM3.6 Kirby AttackAirN — a lingering sex-kick ----
# rukaidata PM3.6 Kirby AttackAirN: 56f total, IASA 43, active 3-29. Two windows
# (per-hitbox active_start/active_end): early f3-6 (dmg 12, BKB 15), late f7-29
# (dmg 9, BKB 0); both angle 55, KBG 100; radii 4.0/2.5u × 5.4 ≈ 22/14, centred
# (offset 0). 4 identical boxes per window collapse to one. Approximated/playtest.
_BIRKY_NAIR = MoveData(
    name="nair",
    in_air=True,
    startup=2,
    active=27,
    recovery=14,  # active f3-29; 2 + 27 + 14 = 43 (PM3.6 IASA)
    hitboxes=(
        Hitbox(circle=Circle(dx=20, dy=30, r=22), damage=12.0, angle=55,
               base_knockback=15.0, knockback_growth=100.0,
               active_start=3, active_end=6),
        Hitbox(circle=Circle(dx=20, dy=30, r=14), damage=9.0, angle=55,
               base_knockback=0.0, knockback_growth=100.0,
               active_start=7, active_end=29),
    ),
)

BIRKY_FIGHTER_DATA = FighterData(
    # hurtbox/posture still reuse the default cat (body geometry is a separate concern);
    # ground normals (#240/#245/#247/#249) + nair (#255).
    hurtbox=_DEFAULT.hurtbox,
    moves={"attack": _BIRKY_DTILT, "jab": _BIRKY_JAB, "ftilt": _BIRKY_FTILT,
           "utilt": _BIRKY_UTILT, "nair": _BIRKY_NAIR},
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
