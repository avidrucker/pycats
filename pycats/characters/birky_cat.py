"""FighterData for "Birky" — the Kirby archetype (floaty featherweight). Slice 1 of #228.

Birky is the **first** fighter to diverge on the per-fighter MOVEMENT SCALARS. Values
from the #229 scoping spike (PM Kirby, proportional-to-Mario; ⚠ pin/playtest later —
hitbox positions follow the #120 approximation convention, see the ⚠ note at `_HURTBOX`):

    weight 70 · gravity 0.42 · max_fall_speed 12 · move_speed 5 · max_jumps 6 · jump_vel -11

Per #120, these scalars are entered RAW (the ×PX_PER_UNIT unit scale is for *spatial* values,
not needed this slice).

Birky owns its full normals + aerials (#240-#260), a Kirby-proportioned `stand_size`
+ body-matched `hurtbox` (#275, a shorter rect — circle shape is a later change), and
the featherweight movement scalars, plus its own Kirby-low crouch/prone geometry (#589).

Caveat (#229): pycats has a single `move_speed` knob (ground == air), so Kirby's
slow-walk / fast-air split can't be captured — `move_speed` leans to the
slow-featherweight identity. The genuine `fast-fall` mechanic is a separate, shared
engine ticket; selectability (making Birky human-pickable) is gated on #117/#127.
"""

from pycats.characters.body_zones import zone_dy
from pycats.combat.data import (
    Circle,
    FieldStatus,
    FighterData,
    Hitbox,
    Hurtbox,
    LandingSpawn,
    MoveData,
    Status,
    VelocityPhase,
    with_dense_hit_labels,
)

# Kirby-proportioned body (#275): shorter than the default 40x60 (Kirby is short/round).
# Shape stays a rect for now (circle is a possible later change). Width kept at 40 so the
# authored horizontal move offsets hold; a fuller re-tune of move dx/dy is a follow-up.
_STAND_SIZE = (40, 44)
_H = _STAND_SIZE[1]  # 44 — Birky's body height, the anchor for every move's dy

# Hitbox dy offsets are ZONE-ANCHORED to _H (#309): the move slices authored them for
# the old 60-tall body, so on the 44 they sat too low (d-tilt hung below the feet, into
# the floor). zone_dy(zone, _H, nudge) re-places each box body-relative — a "feet" poke
# lands at the feet on any body. Every dy below is a ⚠ playtest starting point (ADR-0003);
# faithful OG-derived positions are the #310 spike. dx/radii/frames/scalars are unchanged.
_HURTBOX = Hurtbox(
    circles=(
        Circle(dx=20, dy=13, r=13),  # upper body
        Circle(dx=20, dy=30, r=13),  # lower body
    )
)

# --- Posture geometry (#589, ratified in #565) -------------------------------
# Birky owns its crouch/prone (was inherited from the default cat, authored for the
# 60-tall default body — on Birky's 44 stand the default 40-tall crouch dropped
# only 4px and read as "not really crouching"). The owner ratified "Kirby-low":
# crouch 24 (a 45% drop) / prone 14, leaning into Kirby's low-profile duck.
# The hurtboxes are re-authored to fit the shorter boxes (every circle inside the
# box): combat tests these circles, not just the rect, so the inherited default
# ones — reaching y≈44/23 — would leave a crouching Birky hittable below its body.
_CROUCH_SIZE = (40, 24)
_CROUCH_HURTBOX = Hurtbox(
    circles=(
        Circle(dx=20, dy=10, r=10),  # upper dome, y 0..20
        Circle(dx=20, dy=16, r=8),  # lower body, y 8..24
    )
)
_PRONE_SIZE = (40, 14)
_PRONE_HURTBOX = Hurtbox(
    circles=(
        Circle(dx=16, dy=7, r=7),  # front, lying flat, y 0..14
        Circle(dx=25, dy=7, r=7),  # back, spread along x
    )
)

# --- Jab (slice 2, #240): PM3.6 Kirby jab 1 (Attack11) ------------------------
# rukaidata PM3.6 Kirby Attack11: 16 frames total (IASA 16), hitbox active ~frame 3,
# damage 3.0, angle 361 (Sakurai sentinel), BKB 8, KBG 50 (normal knockback, not
# WDSK). #120 units: frames/%/angle/BKB/KBG RAW; radius 3.13u × PX_PER_UNIT ≈ 17 px. Active
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
        Hitbox(
            circle=Circle(dx=38, dy=zone_dy("center", _H), r=17),
            damage=3.0,
            angle=361,
            base_knockback=8.0,
            knockback_growth=50.0,
        ),
        Hitbox(
            circle=Circle(dx=30, dy=zone_dy("center", _H, 1), r=17),
            damage=3.0,
            angle=361,
            base_knockback=8.0,
            knockback_growth=50.0,
        ),
    ),
)

# --- Down-tilt, mapped to the "attack" slot (slice 2, #245): PM3.6 Kirby AttackLw3 -
# rukaidata PM3.6 Kirby AttackLw3: 30f total, IASA 21, active 4-7; four hitboxes
# (skip the r=0 one), all damage 10, angle 20, BKB 40, KBG 30. #120 units: scalars
# RAW; radii round(size×PX_PER_UNIT) for 3.91/4.69/3.55u ≈ 21/25/19. A low poke → high dy
# (near the feet); dx short (featherweight). dx/dy approximated by convention
# (bone-relative offsets not mapped), flagged for playtest — per nalio_cat.py.
_BIRKY_DTILT = MoveData(
    name="dtilt",
    in_air=False,
    startup=3,
    active=4,
    recovery=14,  # active f4-7; 3 + 4 + 14 = 21 (PM3.6 IASA)
    hitboxes=(
        Hitbox(
            circle=Circle(dx=42, dy=zone_dy("feet", _H), r=25),
            damage=10.0,
            angle=20,
            base_knockback=40.0,
            knockback_growth=30.0,
        ),
        Hitbox(
            circle=Circle(dx=34, dy=zone_dy("feet", _H, 1), r=21),
            damage=10.0,
            angle=20,
            base_knockback=40.0,
            knockback_growth=30.0,
        ),
        Hitbox(
            circle=Circle(dx=28, dy=zone_dy("feet", _H, 2), r=19),
            damage=10.0,
            angle=20,
            base_knockback=40.0,
            knockback_growth=30.0,
        ),
    ),
)

# --- Forward-tilt (slice 2, #247): PM3.6 Kirby AttackS3S -----------------------
# rukaidata PM3.6 Kirby AttackS3S: 33f total, IASA 28, active 5-8; three hitboxes,
# all damage 11, angle 361 (Sakurai), BKB 8, KBG 100 (no WDSK). #120 units: scalars
# RAW; radii round(size×PX_PER_UNIT) for 3.52/3.91/3.75u ≈ 19/21/20. A forward poke → dx
# increasing (offsets 0/3.95/7.7u), mid-height dy. Approximated/playtest per precedent.
_BIRKY_FTILT = MoveData(
    name="ftilt",
    in_air=False,
    startup=4,
    active=4,
    recovery=20,  # active f5-8; 4 + 4 + 20 = 28 (PM3.6 IASA)
    hitboxes=(
        Hitbox(
            circle=Circle(dx=38, dy=zone_dy("center", _H, 1), r=19),
            damage=11.0,
            angle=361,
            base_knockback=8.0,
            knockback_growth=100.0,
        ),
        Hitbox(
            circle=Circle(dx=46, dy=zone_dy("center", _H), r=21),
            damage=11.0,
            angle=361,
            base_knockback=8.0,
            knockback_growth=100.0,
        ),
        Hitbox(
            circle=Circle(dx=52, dy=zone_dy("center", _H), r=20),
            damage=11.0,
            angle=361,
            base_knockback=8.0,
            knockback_growth=100.0,
        ),
    ),
)


# --- Up-tilt (slice 2, #249): PM3.6 Kirby AttackHi3 — a two-window upward poke -----
# rukaidata PM3.6 Kirby AttackHi3: 24f total, IASA 24, active 4-10. Two windows
# (per-hitbox active_start/active_end, like nalio_cat.py u-air): early f4-5 (dmg 8,
# angle 92), late f6-10 (dmg 6, angle 88); both BKB 40, KBG 118/114; sizes 4.69/5.47u
# → radii ≈ 25/30 (×PX_PER_UNIT). Hits above the cat (low dy, near/over the head), centred dx.
# Approximated/playtest per precedent. #120 units: scalars RAW, radius ×PX_PER_UNIT.
def _utilt_box(dx, dy, r, damage, angle, kbg, start, end):
    return Hitbox(
        circle=Circle(dx=dx, dy=dy, r=r),
        damage=damage,
        angle=angle,
        base_knockback=40.0,
        knockback_growth=kbg,
        active_start=start,
        active_end=end,
        set_id=1,  # B-full (#888): both windows share one set → hit a target once
    )


_BIRKY_UTILT = MoveData(
    name="utilt",
    in_air=False,
    startup=3,
    active=7,
    recovery=14,  # active f4-10; 3 + 7 + 14 = 24 (PM3.6 IASA)
    hitboxes=(
        _utilt_box(dx=22, dy=zone_dy("head", _H), r=25, damage=8.0, angle=92, kbg=118.0, start=4, end=5),
        _utilt_box(dx=30, dy=zone_dy("head", _H, 2), r=30, damage=8.0, angle=92, kbg=114.0, start=4, end=5),
        _utilt_box(dx=22, dy=zone_dy("head", _H), r=25, damage=6.0, angle=88, kbg=118.0, start=6, end=10),
        _utilt_box(dx=30, dy=zone_dy("head", _H, 2), r=30, damage=6.0, angle=88, kbg=114.0, start=6, end=10),
    ),
)

# --- Neutral-air (slice 3, #255): PM3.6 Kirby AttackAirN — was a lingering sex-kick -
# FLATTENED to a single window for V1 (#911, ruling on #893): the sex kick (early f3-6
# dmg 12/BKB 15 -> late f7-29 dmg 9/BKB 0; both angle 55, KBG 100) is deferred post-V1.
# One window spans the full active duration f3-29; damage=avg(12,9)=10.5,
# BKB=avg(15,0)=7.5; angle/KBG were equal across the windows, so they carry through.
# Spatial layout keeps the CLEAN box (r=22; the late box was the smaller r=14).
# human-designer-temporary-placeholder-values-for-v1-only — NO parity claim; the basis
# is the #893 designer decision, restored to the two-window falloff post-V1.
_BIRKY_NAIR = MoveData(
    name="nair",
    in_air=True,
    startup=2,
    active=27,
    recovery=14,  # active f3-29; 2 + 27 + 14 = 43 (PM3.6 IASA)
    hitboxes=(
        Hitbox(
            circle=Circle(dx=20, dy=zone_dy("center", _H), r=22),
            damage=10.5,  # avg(12, 9)
            angle=55,
            base_knockback=7.5,  # avg(15, 0)
            knockback_growth=100.0,
            active_start=3,
            active_end=29,
        ),
    ),
)


# --- Forward-air (slice 3, #256): PM3.6 Kirby AttackAirF — 3-window multihit -------
# rukaidata PM3.6 Kirby AttackAirF: 51f total, IASA 40. Drag hits f7-8 & f14-15
# (dmg 5, angle 60/75, set_knockback/WDSK 30, BKB 0, KBG 100) + a Sakurai finisher
# f22-24 (dmg 7, angle 361, KBG 160). Radii round(size×PX_PER_UNIT) for 4.75/4.69/4.5/5.5u.
# Forward dx; mid dy. Approximated/playtest per #120; WDSK like nalio_cat.py jab.
def _fair_box(dx, dy, r, damage, angle, kbg, start, end, wdsk=None):
    return Hitbox(
        circle=Circle(dx=dx, dy=dy, r=r),
        damage=damage,
        angle=angle,
        base_knockback=0.0,
        knockback_growth=kbg,
        set_knockback=wdsk,
        active_start=start,
        active_end=end,
    )


_BIRKY_FAIR = MoveData(
    name="fair",
    in_air=True,
    startup=6,
    active=18,
    recovery=16,  # active f7-24; 6 + 18 + 16 = 40 (PM3.6 IASA)
    hitboxes=(
        _fair_box(dx=42, dy=zone_dy("center", _H), r=26, damage=5.0, angle=60, kbg=100.0, start=7, end=8, wdsk=30),
        _fair_box(dx=50, dy=zone_dy("center", _H, -2), r=25, damage=5.0, angle=75, kbg=100.0, start=7, end=8, wdsk=30),
        _fair_box(dx=42, dy=zone_dy("center", _H), r=24, damage=5.0, angle=60, kbg=100.0, start=14, end=15, wdsk=30),
        _fair_box(
            dx=50, dy=zone_dy("center", _H, -2), r=25, damage=5.0, angle=75, kbg=100.0, start=14, end=15, wdsk=30
        ),
        _fair_box(dx=50, dy=zone_dy("center", _H, -1), r=30, damage=7.0, angle=361, kbg=160.0, start=22, end=24),
        _fair_box(dx=42, dy=zone_dy("center", _H), r=30, damage=7.0, angle=361, kbg=160.0, start=22, end=24),
    ),
)


# --- Back-air (slice 3, #258): PM3.6 Kirby AttackAirB — was a 2-window backward hit -
# FLATTENED to a single window for V1 (#911, ruling on #893): the sex kick (early f6-8
# dmg 14/BKB 10 -> late f9-20 dmg 10/BKB 0; both angle 361, KBG 100) is deferred
# post-V1. One window spans f6-20; damage=avg(14,10)=12, BKB=avg(10,0)=5; angle/KBG
# were equal across the windows. Spatial layout keeps the CLEAN boxes (r=30/32; the
# late boxes were the smaller r=27/23). Behind the cat (dx < 0).
# human-designer-temporary-placeholder-values-for-v1-only — NO parity claim; the basis
# is the #893 designer decision, restored to the two-window falloff post-V1.
def _bair_box(dx, dy, r):
    return Hitbox(
        circle=Circle(dx=dx, dy=dy, r=r),
        damage=12.0,  # avg(14, 10)
        angle=361,
        base_knockback=5.0,  # avg(10, 0)
        knockback_growth=100.0,
        active_start=6,
        active_end=20,
    )


_BIRKY_BAIR = MoveData(
    name="bair",
    in_air=True,
    startup=5,
    active=15,
    recovery=16,  # active f6-20; 5 + 15 + 16 = 36 (PM3.6 IASA)
    hitboxes=(
        _bair_box(dx=-12, dy=zone_dy("center", _H), r=30),
        _bair_box(dx=-2, dy=zone_dy("center", _H, 3), r=32),
    ),
)

# --- Up-air (slice 3, #259): PM3.6 Kirby AttackAirHi — was a 2-window juggle --------
# FLATTENED to a single window for V1 (#911, ruling on #893): the juggle (early f10-12
# dmg 15/ang 75/BKB 5/KBG 115 -> late f13-15 dmg 12/ang 30/BKB 10/KBG 90) is deferred
# post-V1. One window spans f10-15; damage=avg(15,12)=13.5, BKB=avg(5,10)=7.5,
# KBG=avg(115,90)=102.5; angle keeps the CLEAN window's 75 (the windows differed
# 75 vs 30 — not averaged). Spatial layout keeps the CLEAN two-box pair (dx=20, dx=28;
# the late window was a single box at dx=24). Above the cat (low dy).
# human-designer-temporary-placeholder-values-for-v1-only — NO parity claim; the basis
# is the #893 designer decision, restored to the two-window falloff post-V1.
_BIRKY_UAIR = MoveData(
    name="uair",
    in_air=True,
    startup=9,
    active=6,
    recovery=21,  # active f10-15; 9 + 6 + 21 = 36 (PM3.6 IASA)
    hitboxes=(
        Hitbox(
            circle=Circle(dx=20, dy=zone_dy("head", _H), r=23),
            damage=13.5,  # avg(15, 12)
            angle=75,  # clean window's angle (late was 30 — not averaged)
            base_knockback=7.5,  # avg(5, 10)
            knockback_growth=102.5,  # avg(115, 90)
            active_start=10,
            active_end=15,
        ),
        Hitbox(
            circle=Circle(dx=28, dy=zone_dy("head", _H), r=23),
            damage=13.5,  # avg(15, 12)
            angle=75,  # clean window's angle (late was 30 — not averaged)
            base_knockback=7.5,  # avg(5, 10)
            knockback_growth=102.5,  # avg(115, 90)
            active_start=10,
            active_end=15,
        ),
    ),
)

# --- Down-air (slice 3, #260): PM3.6 Kirby AttackAirLw — a looping spike drill ------
# rukaidata PM3.6 Kirby AttackAirLw: 55f total, IASA 50; active windows 13-14/16-17/
# 19-20/22-23/25-26/28-29 (2 active / 1 gap → rehit every 3 frames). All hits dmg 3,
# angle 270 (down spike), BKB 10, KBG 100; 2 hitboxes, radii round(size×PX_PER_UNIT) for
# 6.05/4.69u ≈ 33/25, BELOW the cat (high dy). rehit_rate like nalio d-air. Playtest.
_BIRKY_DAIR = MoveData(
    name="dair",
    in_air=True,
    startup=12,
    active=17,
    recovery=21,  # active f13-29; 12 + 17 + 21 = 50 (PM3.6 IASA)
    rehit_rate=3,  # 2-active / 1-gap loop → rehit every 3 frames (⚠ playtest start)
    hitboxes=(
        Hitbox(
            circle=Circle(dx=18, dy=zone_dy("below_feet", _H), r=33),
            damage=3.0,
            angle=270,
            base_knockback=10.0,
            knockback_growth=100.0,
            active_start=13,
            active_end=29,
        ),
        Hitbox(
            circle=Circle(dx=26, dy=zone_dy("below_feet", _H, 4), r=25),
            damage=3.0,
            angle=270,
            base_knockback=10.0,
            knockback_growth=100.0,
            active_start=13,
            active_end=29,
        ),
    ),
)

# --- Smashes (#459, child of #228): Birky's f/u/d-smash --------------------------
# Short-range, single-box-per-window grounded smashes, chargeable via the mechanic in
# #371/#377 (scaled at spawn, damage-only per #437). Values are PM3.6-Kirby-shaped
# (rukaidata AttackS4S / AttackHi4 / AttackLw4): frames/%/angle/BKB/KBG entered RAW
# (#120); dx/dy short-reach (featherweight) + zone-anchored (#309), radii round(size×
# PX_PER_UNIT). All ⚠ playtest starting points (ADR-0003); faithful px is the #310 spike.
# Angleable f-smash is engine-side: any move keyed "fsmash" gets the global
# FSMASH_ANGLE_UP/DOWN when held up/down (#383) — no per-character field here.

# Forward-smash (AttackS4S): a strong early hit (f8-14) → weaker, higher-launching late
# hit (f15-17). Short reach; the Kirby fsmash is a stubby but committed KO poke.
_BIRKY_FSMASH = MoveData(
    name="fsmash",
    in_air=False,
    chargeable=True,
    startup=7,
    active=10,  # active window f8-17
    recovery=22,  # 7 + 10 + 22 = 39
    hitboxes=(
        Hitbox(
            circle=Circle(dx=44, dy=zone_dy("center", _H), r=24),
            damage=15.0,
            angle=38,
            base_knockback=40.0,
            knockback_growth=100.0,
            active_start=8,
            active_end=14,
            set_id=1,  # B-full (#888): clean+late one set → hit once
        ),
        Hitbox(
            circle=Circle(dx=44, dy=zone_dy("center", _H), r=22),
            damage=13.0,
            angle=73,
            base_knockback=25.0,
            knockback_growth=100.0,
            active_start=15,
            active_end=17,
            set_id=1,
        ),
    ),
)

# Up-smash (AttackHi4): an overhead flip-kick arc — the strong early hit (f6-8) launches
# near-vertical; a weak "sour" late hit (f9-13) follows. Anti-air / juggle starter.
_BIRKY_USMASH = MoveData(
    name="usmash",
    in_air=False,
    chargeable=True,
    startup=5,
    active=8,  # active window f6-13
    recovery=22,  # 5 + 8 + 22 = 35 (PM3.6 IASA 35)
    hitboxes=(
        Hitbox(
            circle=Circle(dx=20, dy=zone_dy("head", _H, -2), r=24),
            damage=15.0,
            angle=88,
            base_knockback=30.0,
            knockback_growth=120.0,
            active_start=6,
            active_end=8,
            set_id=1,  # B-full (#888): clean+late one set → hit once
        ),
        Hitbox(
            circle=Circle(dx=22, dy=zone_dy("head", _H), r=22),
            damage=13.0,
            angle=70,
            base_knockback=12.0,
            knockback_growth=55.0,
            active_start=9,
            active_end=13,
            set_id=1,
        ),
    ),
)

# Down-smash (AttackLw4): a splits kick — FRONT and BACK boxes live TOGETHER (not Marth's
# front-then-back split), with an early (f4-10) → late (f11-18) damage falloff. Front hits
# harder/steeper (50deg), back is the low sweep (28deg).
_BIRKY_DSMASH = MoveData(
    name="dsmash",
    in_air=False,
    chargeable=True,
    startup=3,
    active=15,  # active window f4-18
    recovery=29,  # 3 + 15 + 29 = 47 (PM3.6 IASA 47)
    hitboxes=(
        # Early window f4-10 (front + back simultaneous).
        # B-full (#888): all four boxes share set_id=1 — a target on either side is
        # hit once (early OR late), and two targets (one per side) still each take
        # one hit since the registry keys on (set_id, target).
        Hitbox(
            circle=Circle(dx=40, dy=zone_dy("feet", _H), r=21),
            damage=14.0,
            angle=50,
            base_knockback=30.0,
            knockback_growth=100.0,
            active_start=4,
            active_end=10,
            set_id=1,
        ),
        Hitbox(
            circle=Circle(dx=-40, dy=zone_dy("feet", _H), r=23),
            damage=14.0,
            angle=28,
            base_knockback=20.0,
            knockback_growth=85.0,
            active_start=4,
            active_end=10,
            set_id=1,
        ),
        # Late window f11-18 (weaker).
        Hitbox(
            circle=Circle(dx=40, dy=zone_dy("feet", _H), r=21),
            damage=12.0,
            angle=50,
            base_knockback=30.0,
            knockback_growth=100.0,
            active_start=11,
            active_end=18,
            set_id=1,
        ),
        Hitbox(
            circle=Circle(dx=-40, dy=zone_dy("feet", _H), r=23),
            damage=10.0,
            angle=28,
            base_knockback=20.0,
            knockback_growth=85.0,
            active_start=11,
            active_end=18,
            set_id=1,
        ),
    ),
)


# --- Up-B = Final Cutter (full 3-phase, #969 rise + #973 plunge + #974 shockwave) ----
# Birky's recovery special: a canonical 3-phase move on ONE MoveData under the ratified
# #1066 phase model C (per-frame behavior = MoveData + MoveClock; the whole move is a
# single move-instance). Rise sourced from PM3.6 Kirby `SpecialAirHi2` via the
# brawllib_rs datamine (docs/research/2026-07-31-birky-final-cutter-sourcing.md); the
# phase-2/3 numbers below are the per-cat DATA (#1110) wired onto the engine hooks
# #973 (mid-move velocity flip) / #974 (landing spawn) — playtest starting points,
# tuned in task 3 of the #1095 tracker.
#
# Phase 1 — rising slash + upward burst (#969, datamine phase-1, active f3-4): 4 boxes,
# all `set_id`-shared so first-box-wins (#130) lands exactly ONE — an 8% hit, WDSK
# 117/102, KBG 100, angle ~80-91, effect Slash. Radius u(3.5)=19 maps cleanly; dx/dy
# are body-fit `⚠ playtest starting point`s (raw forward reach u(18)=97 is far too long
# for Birky's small featherweight body — drawn in to short-reach + zone-anchored,
# #309/ADR-0003). recovery_vy = -15.7: the datamined apex rise 292.3px (∫ root velocity,
# ≈2.03x jump) back-solved through Birky's gravity 0.42 (v=√(2·g·h)). recovery_vx = 0:
# root-motion x is 0.0 on every frame — Final Cutter is purely vertical (canon).
#
# Phase 2 — descending plunge + spike (#973): a VelocityPhase SETs a fast downward
# velocity at the burst APEX. Apex ≈ f38: the -15.7 burst is cancelled by gravity 0.42
# after 15.7/0.42 ≈ 37.4 frames (⚠ ADR-0003-class playtest frame, NOT the datamine's
# f19 — that's a different animation's timing; pycats' apex is a function of our own
# recovery_vy/gravity). plunge vy = 12.0 = Birky's max_fall_speed: `apply_gravity`
# clamps vel.y to max_fall_speed each physics step, so 12 is the fastest a DATA-only
# plunge can descend (a snap to terminal at apex vs the floaty gravity ease-in — the
# visible plunge). A faster-than-terminal plunge needs the fast-fall engine work
# (#1068), out of scope here. The downward `_fc_spike` box (angle 270) is active across
# the plunge window (f38-44), a meteor as the drop initiates.
#
# Phase 3 — landing shockwave (#974): a LandingSpawn fires a feet-level ground beam on
# the touchdown EVENT (not a move-clock frame — descent-to-floor distance varies).
# both_directions → a symmetric pair; landing_lag 35 = PM `SpecialAirHi4` end-lag,
# routed through the `landing_lag` chart state -> idle. speed/lifetime are ⚠ playtest
# starting points. By touchdown the move has ended (routed to helpless mid-descent);
# the descriptor is stashed at move start, so it survives the move-clock clearing.
def _fc_slash(dx, dy, r, angle, wdsk):
    # A rising-slash box: WDSK (weight-dependent set) knockback, KBG 100, 8%, active
    # f3-4. All four share one window -> first-box-wins picks one -> a single hit.
    #
    # Value status (#1133 seam, ratified #1129) — this is the MIXED box #1124 named:
    # the datamine (docs/research/2026-07-31-birky-final-cutter-sourcing.md) sources
    # the radius (u(3.5)=19), damage (8%), angle (~80-91), KBG (100) and WDSK
    # (117/102); only dx/dy are body-fit playtest starting points (drawn in from the
    # raw u(18) forward reach, #309/ADR-0003). So within ONE box the circle's `r` is
    # FOUND while its `dx`/`dy` are PLACEHOLDER — the per-value granularity #1129 Q5.
    return Hitbox(
        circle=Circle(
            dx=dx,
            dy=dy,
            r=r,
            status={
                "r": FieldStatus(Status.FOUND, "datamine"),  # u(3.5)=19 maps cleanly
                "dx": FieldStatus(Status.PLACEHOLDER),  # body-fit playtest (#309)
                "dy": FieldStatus(Status.PLACEHOLDER),
            },
        ),
        damage=8.0,
        angle=angle,
        base_knockback=0.0,
        knockback_growth=100.0,
        set_knockback=wdsk,
        active_start=3,
        active_end=4,
        status={
            "damage": FieldStatus(Status.FOUND, "datamine"),  # 8%
            "angle": FieldStatus(Status.FOUND, "datamine"),  # ~80-91
            "knockback_growth": FieldStatus(Status.FOUND, "datamine"),  # KBG 100
            "set_knockback": FieldStatus(Status.FOUND, "datamine"),  # WDSK 117/102
        },
    )


# The plunge spike (#973 phase 2): a single downward (angle 270) meteor box, centre at
# the feet (r=22 reaches below the body), active across the plunge window f38-44. Centre
# stays on-body per the #309 body-fit guard. Scalars are ⚠ playtest starting points.
# Value status (#1133): phase 2 is entirely playtest starting points (#1110) wired
# onto the #973 hook — NO parity claim, so every value is PLACEHOLDER (distinct from
# GUESS; #1129 Q3), the deliberate V1 stand-in tuned in task 3 of the #1095 tracker.
_fc_spike = Hitbox(
    circle=Circle(
        dx=0,
        dy=zone_dy("feet", _H),
        r=22,
        status={
            "r": FieldStatus(Status.PLACEHOLDER),
            "dx": FieldStatus(Status.PLACEHOLDER),
            "dy": FieldStatus(Status.PLACEHOLDER),
        },
    ),
    damage=6.0,
    angle=270,  # straight-down spike/meteor (same convention as d-air)
    base_knockback=30.0,
    knockback_growth=80.0,
    active_start=38,  # apex/plunge onset
    active_end=44,  # == move total (2+2+40); the plunge window closes as the move ends
    status={
        "damage": FieldStatus(Status.PLACEHOLDER),
        "angle": FieldStatus(Status.PLACEHOLDER),
        "base_knockback": FieldStatus(Status.PLACEHOLDER),
        "knockback_growth": FieldStatus(Status.PLACEHOLDER),
    },
)

# The landing shockwave (#974 phase 3): a feet-level ground beam, mirrored both ways.
# dx=0 (body-centred) because both_directions resolves the same circle against each
# facing. Scalars (speed/lifetime/damage/knockback) are ⚠ playtest starting points;
# landing_lag 35 = PM `SpecialAirHi4`.
_fc_shockwave = LandingSpawn(
    hitboxes=(
        Hitbox(
            circle=Circle(dx=0, dy=zone_dy("feet", _H), r=18),
            damage=5.0,
            angle=45,  # launch up-and-out along travel
            base_knockback=25.0,
            knockback_growth=70.0,
        ),
    ),
    speed=8.0,
    lifetime=20,
    landing_lag=35,  # PM SpecialAirHi4 end-lag
    both_directions=True,
    gravity=0.0,  # a flat ground beam
)


_BIRKY_FINAL_CUTTER = MoveData(
    name="final cutter",
    in_air=True,  # aerial special — does not clank (#133)
    startup=2,
    active=2,
    recovery=40,  # total 44: rise slash f3-4 -> ascent to apex -> plunge/spike f38-44
    grants_recovery=True,
    recovery_vy=-15.7,  # apex 292.3px (∫ root vel, §2) back-solved at g=0.42: √(2·g·h)
    recovery_vx=0.0,  # purely vertical — datamine root-motion x = 0.0 every frame
    hitboxes=(
        # phase 1 blade: 2 heights (head / above-head) x 2 forward reaches, r=u(3.5)=19
        _fc_slash(dx=18, dy=zone_dy("head", _H), r=19, angle=80, wdsk=117),  # id0 near-low (wins)
        _fc_slash(dx=38, dy=zone_dy("head", _H), r=19, angle=91, wdsk=117),  # id1 far-low
        _fc_slash(dx=14, dy=zone_dy("head", _H, -14), r=19, angle=90, wdsk=102),  # id2 near-high
        _fc_slash(dx=32, dy=zone_dy("head", _H, -14), r=19, angle=91, wdsk=102),  # id3 far-high
        _fc_spike,  # phase 2 descending spike (f38-44)
    ),
    velocity_phases=(
        VelocityPhase(frame=38, vx=0.0, vy=12.0),  # phase 2 plunge SET at apex (vy = max_fall_speed cap)
    ),
    landing_spawn=_fc_shockwave,  # phase 3 touchdown ground beam
    # MOVE-level value status (#1133): recovery_vy = -15.7 is FOUND — the datamined
    # phase-1 apex rise (292.3px, ∫ root velocity) back-solved through Birky's gravity
    # (√(2·g·h)); its source is the brawllib_rs datamine, not playtest.
    status={
        "recovery_vy": FieldStatus(Status.FOUND, "datamine"),
    },
)

# --- Idle rest loop (#1105, Decision A #1104) ---------------------------------
# Idle as a first-class MoveData so it flows through the standard move pipeline (editor
# move cycle / timeline / scrubber / reference-GIF layer) like every attack — no bespoke
# idle mechanism. No active hitbox window → empty hitboxes; the posture stand hurtbox
# (_HURTBOX) already covers idle (#1082), so no per-move hurtbox override. Loop length =
# PM Marth `Wait1` subaction, brawllib_rs datamine (env #614): 71 frames (FOUND). Modeled
# as recovery with startup = active = 0.
_WAIT = MoveData(name="wait", in_air=False, startup=0, active=0, recovery=71, hitboxes=())

BIRKY_FIGHTER_DATA = FighterData(
    # own Kirby-sized body (#275) + body-matched hurtbox; own Kirby-low crouch/prone (#589);
    # ground normals (#240/#245/#247/#249) + aerials nair #255 / fair #256 / bair #258
    # / uair #259 / dair #260 — Birky's full normals + aerials.
    hurtbox=_HURTBOX,
    stand_size=_STAND_SIZE,
    moves={
        "attack": _BIRKY_DTILT,
        "jab": _BIRKY_JAB,
        "ftilt": _BIRKY_FTILT,
        "utilt": _BIRKY_UTILT,
        "nair": _BIRKY_NAIR,
        "fair": _BIRKY_FAIR,
        "bair": _BIRKY_BAIR,
        "uair": _BIRKY_UAIR,
        "dair": _BIRKY_DAIR,
        "fsmash": _BIRKY_FSMASH,
        "usmash": _BIRKY_USMASH,
        "dsmash": _BIRKY_DSMASH,
        "up_b": _BIRKY_FINAL_CUTTER,  # Final Cutter, rise-only (#969)
        "wait": _WAIT,  # idle rest loop (#1105)
    },
    crouch_size=_CROUCH_SIZE,
    crouch_hurtbox=_CROUCH_HURTBOX,
    prone_size=_PRONE_SIZE,
    prone_hurtbox=_PRONE_HURTBOX,
    # the featherweight movement scalars (#229)
    weight=70,
    gravity=0.42,
    max_fall_speed=12,
    move_speed=5,
    max_jumps=6,
    jump_vel=-11,
)

# #1041: stamp dense A,B,C hit-box labels — the baseline labeling for authored
# data — so the shipped JSON carries the real `label`s the editor adopts (#1030).
BIRKY_FIGHTER_DATA = with_dense_hit_labels(BIRKY_FIGHTER_DATA)
