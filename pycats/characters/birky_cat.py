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

# --- Forward-air (slice 3, #256): PM3.6 Kirby AttackAirF — 3-window multihit -------
# rukaidata PM3.6 Kirby AttackAirF: 51f total, IASA 40. Drag hits f7-8 & f14-15
# (dmg 5, angle 60/75, set_knockback/WDSK 30, BKB 0, KBG 100) + a Sakurai finisher
# f22-24 (dmg 7, angle 361, KBG 160). Radii round(size×5.4) for 4.75/4.69/4.5/5.5u.
# Forward dx; mid dy. Approximated/playtest per #120; WDSK like nalio_cat.py jab.
def _fair_box(dx, dy, r, damage, angle, kbg, start, end, wdsk=None):
    return Hitbox(circle=Circle(dx=dx, dy=dy, r=r), damage=damage, angle=angle,
                  base_knockback=0.0, knockback_growth=kbg,
                  set_knockback=wdsk, active_start=start, active_end=end)


_BIRKY_FAIR = MoveData(
    name="fair",
    in_air=True,
    startup=6,
    active=18,
    recovery=16,  # active f7-24; 6 + 18 + 16 = 40 (PM3.6 IASA)
    hitboxes=(
        _fair_box(dx=42, dy=30, r=26, damage=5.0, angle=60, kbg=100.0, start=7, end=8, wdsk=30),
        _fair_box(dx=50, dy=28, r=25, damage=5.0, angle=75, kbg=100.0, start=7, end=8, wdsk=30),
        _fair_box(dx=42, dy=30, r=24, damage=5.0, angle=60, kbg=100.0, start=14, end=15, wdsk=30),
        _fair_box(dx=50, dy=28, r=25, damage=5.0, angle=75, kbg=100.0, start=14, end=15, wdsk=30),
        _fair_box(dx=50, dy=29, r=30, damage=7.0, angle=361, kbg=160.0, start=22, end=24),
        _fair_box(dx=42, dy=29, r=30, damage=7.0, angle=361, kbg=160.0, start=22, end=24),
    ),
)

# --- Back-air (slice 3, #258): PM3.6 Kirby AttackAirB — 2-window backward hit ------
# rukaidata PM3.6 Kirby AttackAirB: 41f total, IASA 36, active 6-20. Early f6-8
# (dmg 14, BKB 10), late f9-20 (dmg 10, BKB 0); both angle 361, KBG 100; radii
# round(size×5.4) for 5.5/5.99/5.08/4.3u ≈ 30/32/27/23. Behind the cat (dx < 0,
# mirroring nalio_cat.py bair). Approximated/playtest per #120.
def _bair_box(dx, dy, r, damage, bkb, start, end):
    return Hitbox(circle=Circle(dx=dx, dy=dy, r=r), damage=damage, angle=361,
                  base_knockback=bkb, knockback_growth=100.0,
                  active_start=start, active_end=end)


_BIRKY_BAIR = MoveData(
    name="bair",
    in_air=True,
    startup=5,
    active=15,
    recovery=16,  # active f6-20; 5 + 15 + 16 = 36 (PM3.6 IASA)
    hitboxes=(
        _bair_box(dx=-12, dy=30, r=30, damage=14.0, bkb=10.0, start=6, end=8),
        _bair_box(dx=-2, dy=33, r=32, damage=14.0, bkb=10.0, start=6, end=8),
        _bair_box(dx=-12, dy=30, r=27, damage=10.0, bkb=0.0, start=9, end=20),
        _bair_box(dx=-2, dy=33, r=23, damage=10.0, bkb=0.0, start=9, end=20),
    ),
)

# --- Up-air (slice 3, #259): PM3.6 Kirby AttackAirHi — 2-window juggle -------------
# rukaidata PM3.6 Kirby AttackAirHi: 48f total, IASA 36, active 10-15. Early f10-12
# (dmg 15, angle 75, BKB 5, KBG 115), late f13-15 (dmg 12, angle 30, BKB 10, KBG 90);
# radius round(4.32×5.4) ≈ 23. Above the cat (low dy). Approximated/playtest per #120.
_BIRKY_UAIR = MoveData(
    name="uair",
    in_air=True,
    startup=9,
    active=6,
    recovery=21,  # active f10-15; 9 + 6 + 21 = 36 (PM3.6 IASA)
    hitboxes=(
        Hitbox(circle=Circle(dx=20, dy=6, r=23), damage=15.0, angle=75,
               base_knockback=5.0, knockback_growth=115.0, active_start=10, active_end=12),
        Hitbox(circle=Circle(dx=28, dy=6, r=23), damage=15.0, angle=75,
               base_knockback=5.0, knockback_growth=115.0, active_start=10, active_end=12),
        Hitbox(circle=Circle(dx=24, dy=6, r=23), damage=12.0, angle=30,
               base_knockback=10.0, knockback_growth=90.0, active_start=13, active_end=15),
    ),
)

BIRKY_FIGHTER_DATA = FighterData(
    # hurtbox/posture still reuse the default cat (body geometry is a separate concern);
    # ground normals (#240/#245/#247/#249) + nair (#255) + fair (#256) + bair (#258)
    # + uair (#259).
    hurtbox=_DEFAULT.hurtbox,
    moves={"attack": _BIRKY_DTILT, "jab": _BIRKY_JAB, "ftilt": _BIRKY_FTILT,
           "utilt": _BIRKY_UTILT, "nair": _BIRKY_NAIR, "fair": _BIRKY_FAIR,
           "bair": _BIRKY_BAIR, "uair": _BIRKY_UAIR},
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
