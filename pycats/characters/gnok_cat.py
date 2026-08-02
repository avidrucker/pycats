"""FighterData for "Gnok" — the Donkey-Kong archetype (fast super-heavyweight bruiser).
Slice 1 of 7 under epic #779, per the ratified spec #794 (docs/research-spec-794-gnok-dk-pm.md).

Gnok is the **first cat authored raw-first through the #785 `vel()` seam**: the PM3.6 DK
source *unit rates* stay visible in the source and the ×PX_PER_UNIT factor lives in one
place (combat/units.py). The archetype is a matched pair (spec §1/§3):

- **Fast super-heavyweight** — heaviest cat (weight 114 → dies latest) AND the fastest
  ground mobility + highest jump. PM DK is genuinely heavy *and* mobile; making Gnok slow
  would be the generic trope, not PM3.6.
- **Giant target** — the 76×80 body (spec §2, *measured* from PM3.6 idle hurtbox extents,
  not eyeballed) is the balancing weakness: easy to combo, easy to hit. The big body is
  the intended counterbalance to the fast+heavy stats.

Per #120, combat scalars (weight, max_jumps) are RAW; velocity/accel scalars go through
`vel()` (px-per-frame rates). Values faithful to rukaidata PM3.6 DK (spec §1):

    weight 114 (raw) · move_speed 1.2 · dash_speed 1.8 · jump_vel 2.8 · gravity 0.1
    · max_fall_speed 2.4 · max_jumps 2 (raw)   ← unit rates; vel() scales the spatial ones

Slice 1 authored the scalars + measured body only. Slice 2 (#824) added the **jab** — DK's
1-2 punch (PM3.6 `Attack11` → `Attack12`), modeled as one move with two sequential hit
windows. Slice 3 (#841) added the three **tilts** — f-tilt (`AttackS3S`), u-tilt (`AttackHi3`),
d-tilt (`AttackLw3`). Slices 5-6 (#914) added the five **aerials** — n-air (`AttackAirN`, a sex
kick), f-air (`AttackAirF`, an overhead smash with a late spike), b-air (`AttackAirB`, a Sakurai
sex kick), u-air (`AttackAirHi`, an upward juggle), d-air (`AttackAirLw`, the downward spike).
Slice 7 (#947) adds the three **smashes** — f-smash (`AttackS4S`, a two-hand forward clap),
u-smash (`AttackHi4`, an overhead double-arm clap), d-smash (`AttackLw4`, a two-sided ground
pound); all `chargeable=True`. The remaining slot (dash attack, slice 4) still reuses the
default cat until it lands. Deferred (NOT V1, need engine): grabs/throws, Giant Punch armor,
Spinning Kong recovery (spec §3/§5).

Faithful-physics caveat (#785/#816): pycats' shipped velocity globals are *game-tuned px*,
not rukaidata × 5.4 (e.g. MAX_FALL_SPEED = 13 vs Mario's real ~9.2). Gnok's `vel()` values
are the faithful PM3.6 rates; a roster-wide faithful re-tune is deferred to #816. Gnok does
not block on it — it ships on the same basis the other cats do, just authored via the seam.
"""

from pycats.characters.default_cat import DEFAULT_FIGHTER_DATA as _DEFAULT
from pycats.combat.data import (
    Circle,
    FighterData,
    Hitbox,
    Hurtbox,
    MoveData,
    with_dense_hit_labels,
)
from pycats.combat.units import vel

# --- Stand body (spec §2a/§2b, MEASURED) -------------------------------------
# stand_size (76, 80): PM3.6 idle (Wait1) mean hurtbox extent gave DK ÷ Mario = ×1.92 wide,
# ×1.32 tall; applied to the 40×60 default box → 40×1.92 ≈ 77, 60×1.32 ≈ 79. DK is far
# broader than tall (the hunched, long-armed ape silhouette — nearly square, w/h 0.99).
_STAND_SIZE = (76, 80)

# 4-circle stand hurtbox (spec §2b): DK's 14 idle capsules were dumped in world units,
# converted to pycats coords, and **symmetrized** (the raw dump is one asymmetric idle pose
# — right arm raised — but a pycats hurtbox is static and mirror-flips with facing). Covers
# ~dx 2..74, dy 6..76 — fills the broad box; only extreme corners/foot-tips stay open. A
# denser 6-circle fit is recorded in the #794 grilling if the flanks read too open in playtest.
_HURTBOX = Hurtbox(
    circles=(
        Circle(dx=24, dy=28, r=22),  # upper-left  (head/chest + L arm)
        Circle(dx=52, dy=28, r=22),  # upper-right (head/chest + R arm)
        Circle(dx=24, dy=60, r=16),  # lower-left  (L leg)
        Circle(dx=52, dy=60, r=16),  # lower-right (R leg)
    )
)

# --- Crouch body (spec §2c, MEASURED squash) ---------------------------------
# crouch_size (80, 58): PM3.6 held-duck (SquatWait) vs standing gave DK −27% height, +5%
# width ("DK barely lowers" is true only relative to Mario, who nearly halves). Applied:
# 80×0.73 = 58 tall, 76×1.05 = 80 wide. Gnok is the first cat whose crouch is *wider* than
# its stand (all others hold stand width); the engine takes any (w, h). At 58 tall, Gnok
# crouching ≈ the default cat standing (60) — still huge.
_CROUCH_SIZE = (80, 58)
# The measured squash applied to the 4 stand circles (×80/76 W, ×58/80 H, r×0.889).
_CROUCH_HURTBOX = Hurtbox(
    circles=(
        Circle(dx=25, dy=20, r=20),
        Circle(dx=55, dy=20, r=20),
        Circle(dx=25, dy=44, r=14),  # legs
        Circle(dx=55, dy=44, r=14),
    )
)

# --- Prone body (spec §2d, ⚠ playtest starting point) ------------------------
# Not an archetype lever: a scaled-default lying-flat box for the giant body (default prone
# is 40×22). Fitted 2-circle hurtbox spread across the 80 width, low so high attacks whiff.
# ⚠ playtest-TBD (ADR-0003) — refine when prone reads wrong in-game.
_PRONE_SIZE = (80, 20)
_PRONE_HURTBOX = Hurtbox(
    circles=(
        Circle(dx=30, dy=10, r=10),  # front, lying flat, y 0..20
        Circle(dx=50, dy=10, r=10),  # back, spread along x
    )
)

# --- Jab (slice 2, #824): DK's 1-2 punch (PM3.6 Attack11 → Attack12) ---------
# Gnok's neutral-A is DK's TWO-hit jab (the "heavy-normals 1-2" of epic #779), authored
# as ONE move with two SEQUENTIAL hit windows via per-hitbox active_start/active_end (the
# same #204 engine seam narz's dsmash uses). Hit 1 links, hit 2 launches. This is where
# Gnok's jab diverges from nalio/narz (whose "jab" is Attack11 only) — the spec §6 slice-2
# scope is explicitly Attack11/Attack12.
#
# Datamined at DEV time from the brawllib_rs PM3.6 dump (`-f Donkey -a Attack11/Attack12`,
# `high_level_frame_data -l subaction`; env #614):
#   Attack11 (jab 1): first active frame 3, 4 active frames; 3 boxes, damage 4%,
#                     trajectory 65°, kbg 100, bkb 1, WDSK 20 — a weight-set LINK hit.
#   Attack12 (jab 2): first active frame 6, 6 active frames; 3 boxes, damage 6%,
#                     trajectory 75°, kbg 100, bkb 40, WDSK 0 — the up-forward LAUNCHER.
# Frames / % / angle / BKB / KBG / WDSK entered RAW (#120). Hitbox radii = round(size ×
# PX_PER_UNIT) as for every other cat's moves (nalio/narz convention): jab1 sizes
# 4.69/3.52/2.73 → 25/19/15; jab2 sizes 5.0/4.75/2.73 → 27/26/15 (DK's big fists → big
# radii, reinforcing the heavy feel). Positions dx/dy are APPROXIMATED along the forward
# arm at chest height (no skeleton modeled — same convention as nalio's jab) and remain
# ⚠🔬 playtest starting points (ADR-0003). The two windows are compressed into one move:
# jab1 [3,6], a link gap, jab2 [10,14], then end-lag (total 17).
_GNOK_JAB = MoveData(
    name="jab",
    in_air=False,
    startup=2,  # Attack11 first active frame 3 → 2 startup frames
    active=4,  # jab-1 window (frames 3-6)
    recovery=11,  # total 17; jab-2 fires late (frames 10-14) via active_start, then end-lag
    hitboxes=(
        # --- Hit 1 (Attack11): the forward LINK jab. WDSK 20 / BKB 1 is a weight-set link
        # (#211 set_knockback): it deals 4% but launches a SET distance regardless of the
        # victim's %, keeping the target in range for hit 2 instead of knocking it away.
        Hitbox(
            circle=Circle(dx=82, dy=30, r=25),
            damage=4.0,
            angle=65,
            base_knockback=1.0,
            knockback_growth=100.0,
            set_knockback=20,
            active_start=3,
            active_end=6,
        ),  # fist (id0, size 4.69)
        Hitbox(
            circle=Circle(dx=68, dy=30, r=19),
            damage=4.0,
            angle=65,
            base_knockback=1.0,
            knockback_growth=100.0,
            set_knockback=20,
            active_start=3,
            active_end=6,
        ),  # mid arm (id1, size 3.52)
        Hitbox(
            circle=Circle(dx=56, dy=30, r=15),
            damage=4.0,
            angle=65,
            base_knockback=1.0,
            knockback_growth=100.0,
            set_knockback=20,
            active_start=3,
            active_end=6,
        ),  # inner/shoulder (id2, size 2.73)
        # --- Hit 2 (Attack12): the up-forward LAUNCH finisher (75°, real BKB 40, no WDSK).
        Hitbox(
            circle=Circle(dx=86, dy=26, r=27),
            damage=6.0,
            angle=75,
            base_knockback=40.0,
            knockback_growth=100.0,
            active_start=10,
            active_end=14,
        ),  # fist (id0, size 5.0)
        Hitbox(
            circle=Circle(dx=72, dy=24, r=26),
            damage=6.0,
            angle=75,
            base_knockback=40.0,
            knockback_growth=100.0,
            active_start=10,
            active_end=14,
        ),  # mid arm (id1, size 4.75)
        Hitbox(
            circle=Circle(dx=58, dy=28, r=15),
            damage=6.0,
            angle=75,
            base_knockback=40.0,
            knockback_growth=100.0,
            active_start=10,
            active_end=14,
        ),  # inner (id2, size 2.73)
    ),
)


# --- Forward-tilt (slice 3, #841): DK's AttackS3S, mapped to the "ftilt" key ---
# move_select has one ground-forward key, so the mid/`S3S` variant is authored (the angled
# `AttackS3Hi`/`AttackS3Lw` variants are out of scope — nalio convention). A big forward
# arm-swing: FOUR same-set hitboxes (rukaidata id 0→3), all damage 11, angle 361 (the
# Sakurai sentinel #203, same as nalio's ftilt), BKB 10, KBG 100, WDSK 0 — nothing deferred.
#
# Datamined from the brawllib_rs PM3.6 dump (`-f Donkey -a AttackS3S`) and cross-checked
# against rukaidata (FAF 34, active 8-11):
#   active frames 8-11 (1-indexed) → startup 7 / active 4; FAF 34 → recovery 34-7-4 = 23.
# Frames / % / angle / BKB / KBG entered RAW (#120). Radii = round(size × PX_PER_UNIT):
# 4.0→22, 4.75→26, 4.4→24, 3.52→19 (DK's fist → big radii, the heavy-normal signature).
# Positions dx/dy APPROXIMATED along the forward arm at chest height (no skeleton modeled —
# same convention as the jab/nalio); dx ordered by the datamined forward reach (id1 fist
# furthest, then id0, id2, id3 inner). ⚠🔬 playtest starting points (ADR-0003).
def _ftilt_box(dx, r):
    return Hitbox(
        circle=Circle(dx=dx, dy=32, r=r),
        damage=11.0,
        angle=361,
        base_knockback=10.0,
        knockback_growth=100.0,
    )


_GNOK_FTILT = MoveData(
    name="forward tilt",
    in_air=False,
    startup=7,  # AttackS3S first active frame 8 (1-indexed) → 7 startup frames
    active=4,  # active frames 8-11
    recovery=23,  # FAF 34 → 34 - 7 - 4 = 23
    hitboxes=(
        _ftilt_box(dx=76, r=22),  # id0 (size 4.0) — mid arm
        _ftilt_box(dx=90, r=26),  # id1 (size 4.75) — fist, furthest reach / priority
        _ftilt_box(dx=62, r=24),  # id2 (size 4.4) — inner
        _ftilt_box(dx=48, r=19),  # id3 (size 3.52) — innermost
    ),
)


# --- Up-tilt (slice 3, #841): DK's AttackHi3, mapped to the "utilt" key --------
# An overhead arc: THREE hitboxes (rukaidata id 0→2), angle 100 (an up-and-slightly-back
# launch — a literal angle, NOT a sentinel), BKB 40, WDSK 0. Unlike the same-set f-tilt,
# the boxes escalate: damage 9/10/11 and KBG 105/110/115 (id2 the strongest, the sweetspot).
#
# Datamined from the brawllib_rs PM3.6 dump (`-f Donkey -a AttackHi3`) and cross-checked
# against rukaidata (FAF 36, active 6-11):
#   active frames 6-11 (1-indexed) → startup 5 / active 6; FAF 36 → recovery 36-5-6 = 25.
# Frames / % / angle / BKB / KBG entered RAW (#120). Radii = round(size × PX_PER_UNIT):
# 5.0→27, 3.75→20, 4.0→22. Positions dx/dy APPROXIMATED as an arc clustered above the head
# (small dy — id0 front, id1 directly overhead, id2 back), no skeleton modeled — same
# convention as the jab/f-tilt/nalio. ⚠🔬 playtest starting points (ADR-0003).
def _utilt_box(dx, dy, r, damage, kbg):
    return Hitbox(
        circle=Circle(dx=dx, dy=dy, r=r),
        damage=damage,
        angle=100,
        base_knockback=40.0,
        knockback_growth=kbg,
    )


_GNOK_UTILT = MoveData(
    name="up tilt",
    in_air=False,
    startup=5,  # AttackHi3 first active frame 6 (1-indexed) → 5 startup frames
    active=6,  # active frames 6-11
    recovery=25,  # FAF 36 → 36 - 5 - 6 = 25
    hitboxes=(
        _utilt_box(dx=44, dy=6, r=27, damage=9.0, kbg=105.0),  # id0 (size 5.0) — front
        _utilt_box(dx=36, dy=2, r=20, damage=10.0, kbg=110.0),  # id1 (size 3.75) — overhead
        _utilt_box(dx=28, dy=8, r=22, damage=11.0, kbg=115.0),  # id2 (size 4.0) — back sweetspot
    ),
)


# --- Down-tilt (slice 3, #841): DK's AttackLw3, mapped to the "dtilt" key ------
# A low forward poke (the crouching ankle-sweep): FOUR same-set hitboxes (rukaidata id 0→3),
# all damage 9, angle 40 (a low diagonal — literal, NOT a sentinel), BKB 25, KBG 95, WDSK 0.
#
# Datamined from the brawllib_rs PM3.6 dump (`-f Donkey -a AttackLw3`) and cross-checked
# against rukaidata (FAF 23, active 6-9):
#   active frames 6-9 (1-indexed) → startup 5 / active 4; FAF 23 → recovery 23-5-4 = 14.
# Frames / % / angle / BKB / KBG entered RAW (#120). Radii = round(size × PX_PER_UNIT):
# 3.75→20, 5.4→29, 4.0→22, 3.75→20 (id1 the big low sweep). Positions dx/dy APPROXIMATED
# as a low forward line (larger dy = lower on screen — below the f-tilt line), dx ordered by
# the datamined forward reach (id1 furthest, then id3, id0, id2 inner); no skeleton modeled.
# ⚠🔬 playtest starting points (ADR-0003).
def _dtilt_box(dx, dy, r):
    return Hitbox(
        circle=Circle(dx=dx, dy=dy, r=r),
        damage=9.0,
        angle=40,
        base_knockback=25.0,
        knockback_growth=95.0,
    )


_GNOK_DTILT = MoveData(
    name="down tilt",
    in_air=False,
    startup=5,  # AttackLw3 first active frame 6 (1-indexed) → 5 startup frames
    active=4,  # active frames 6-9
    recovery=14,  # FAF 23 → 23 - 5 - 4 = 14
    hitboxes=(
        _dtilt_box(dx=56, dy=52, r=20),  # id0 (size 3.75)
        _dtilt_box(dx=84, dy=50, r=29),  # id1 (size 5.4) — big low sweep, furthest / priority
        _dtilt_box(dx=44, dy=54, r=22),  # id2 (size 4.0) — inner
        _dtilt_box(dx=70, dy=52, r=20),  # id3 (size 3.75)
    ),
)


# --- N-air (slices 5-6, #914): DK's AttackAirN — a "sex kick" -----------------
# Gnok's neutral aerial is the classic DK sex kick: one strong EARLY window then a long
# WEAK lingering window, authored as two #204 temporal windows (the same seam bair/fair use).
# Datamined at DEV time from the brawllib_rs PM3.6 dump (`-f Donkey -a AttackAirN`,
# `high_level_frame_data -l subaction`; env #614):
#   FAF 36; first active frame 7, last active frame 24 → startup 6 / active 18 / recovery 12.
#   EARLY [7,10]:  3 boxes, damage 14, trajectory 361 (Sakurai), BKB 20, KBG 100, WDSK 0.
#   LATE  [11,24]: damage 10, trajectory 50 (up-forward), BKB 10, KBG 100 — the lingering hit.
# Frames / % / angle / BKB / KBG entered RAW (#120). The 3 raw boxes collapse to 2 distinct
# sizes per window (id0/id1 share a size); radii = round(size u × PX_PER_UNIT): early 6.0→32,
# 7.0→38; late 5.0→27, 6.0→32 (DK's big limbs → big radii). Positions dx/dy APPROXIMATED
# around the spinning body (no skeleton modeled) — a front box + a low sweep; ⚠🔬 playtest
# starting points (ADR-0003).
def _nair_early(dx, dy, r):
    return Hitbox(
        circle=Circle(dx=dx, dy=dy, r=r),
        damage=14.0,
        angle=361,
        base_knockback=20.0,
        knockback_growth=100.0,
        active_start=7,
        active_end=10,
    )


def _nair_late(dx, dy, r):
    return Hitbox(
        circle=Circle(dx=dx, dy=dy, r=r),
        damage=10.0,
        angle=50,
        base_knockback=10.0,
        knockback_growth=100.0,
        active_start=11,
        active_end=24,
    )


_GNOK_NAIR = MoveData(
    name="neutral air",
    in_air=True,
    startup=6,
    active=18,
    recovery=12,
    hitboxes=(
        _nair_early(dx=78, dy=40, r=32),  # early — front limb
        _nair_early(dx=52, dy=64, r=38),  # early — low sweep (bigger box)
        _nair_late(dx=78, dy=40, r=27),  # late — front limb (weak)
        _nair_late(dx=52, dy=64, r=32),  # late — low sweep (weak)
    ),
)


# --- F-air (slices 5-6, #914): DK's AttackAirF — a two-hand overhead smash ----
# Two #204 windows: an EARLY link then a LATE spike finisher. Datamined at DEV time
# (`-f Donkey -a AttackAirF`, high_level_frame_data -l subaction; env #614):
#   FAF 48; active frames 23-27 → startup 22 / active 5 / recovery 21.
#   EARLY [23,25]: 4 boxes, damage 17, trajectory 361 (Sakurai), BKB 20, KBG 100.
#   LATE  [26,27]: the big boxes swing to trajectory 290 (down-forward SPIKE) at BKB 50 /
#                  KBG 73; the small link boxes keep 361 but also jump to BKB 50 / KBG 73.
# Frames/%/angle/BKB/KBG RAW (#120). The 4 raw boxes collapse to 2 distinct sizes per window
# (id0/id1 share, id2/id3 share); radii = round(size u × PX_PER_UNIT): early 7.5→40, 3.2→17;
# late 6.4→35, 3.2→17. Positions APPROXIMATED as an overhead arc swung forward-then-down (no
# skeleton modeled) — ⚠🔬 playtest starting points (ADR-0003).
def _fair_early(dx, dy, r):
    return Hitbox(
        circle=Circle(dx=dx, dy=dy, r=r),
        damage=17.0,
        angle=361,
        base_knockback=20.0,
        knockback_growth=100.0,
        active_start=23,
        active_end=25,
    )


def _fair_late(dx, dy, r, angle):
    # BKB 50 / KBG 73 for both late boxes; the big box spikes at 290, the link stays 361.
    return Hitbox(
        circle=Circle(dx=dx, dy=dy, r=r),
        damage=17.0,
        angle=angle,
        base_knockback=50.0,
        knockback_growth=73.0,
        active_start=26,
        active_end=27,
    )


_GNOK_FAIR = MoveData(
    name="forward air",
    in_air=True,
    startup=22,
    active=5,
    recovery=21,
    hitboxes=(
        _fair_early(dx=72, dy=22, r=40),  # early — big overhead arc
        _fair_early(dx=84, dy=42, r=17),  # early — forward link
        _fair_late(dx=74, dy=52, r=35, angle=290),  # late — the down-forward SPIKE
        _fair_late(dx=84, dy=36, r=17, angle=361),  # late — link (Sakurai)
    ),
)


# --- B-air (slices 5-6, #914): DK's AttackAirB — a Sakurai-angle sex kick -----
# Behind-the-body back kick; both windows launch at the 361 Sakurai sentinel, decaying in
# damage/knockback (a #204 clean→late sex kick). Datamined (`-f Donkey -a AttackAirB`,
# high_level_frame_data -l subaction; env #614):
#   FAF 31; active frames 7-20 → startup 6 / active 14 / recovery 11.
#   CLEAN [7,8]:  2 boxes, damage 13, angle 361, BKB 20, KBG 100.
#   LATE  [9,20]: damage 9, angle 361, BKB 10, KBG 100 — the long lingering hit.
# Frames/%/angle/BKB/KBG RAW (#120); radii = round(size u × PX_PER_UNIT): clean 5.86→32,
# 3.91→21; late 5.47→30, 3.52→19. Positions APPROXIMATED behind the body (dx < body width —
# b-air hits backward; the sim mirror-flips with facing) — ⚠🔬 playtest (ADR-0003).
def _bair_clean(dx, dy, r):
    return Hitbox(
        circle=Circle(dx=dx, dy=dy, r=r),
        damage=13.0,
        angle=361,
        base_knockback=20.0,
        knockback_growth=100.0,
        active_start=7,
        active_end=8,
    )


def _bair_late(dx, dy, r):
    return Hitbox(
        circle=Circle(dx=dx, dy=dy, r=r),
        damage=9.0,
        angle=361,
        base_knockback=10.0,
        knockback_growth=100.0,
        active_start=9,
        active_end=20,
    )


_GNOK_BAIR = MoveData(
    name="back air",
    in_air=True,
    startup=6,
    active=14,
    recovery=11,
    hitboxes=(
        _bair_clean(dx=-10, dy=40, r=32),  # clean — rear foot (bigger)
        _bair_clean(dx=6, dy=42, r=21),  # clean — inner leg
        _bair_late(dx=-10, dy=40, r=30),  # late — rear foot (weak)
        _bair_late(dx=6, dy=42, r=19),  # late — inner leg (weak)
    ),
)

# --- U-air (slices 5-6, #914): DK's AttackAirHi — a straight-up juggle --------
# A single-window upward headbutt (no early/late decay). Datamined (`-f Donkey -a
# AttackAirHi`, high_level_frame_data -l subaction; env #614):
#   FAF 37; active frames 6-9 → startup 5 / active 4 / recovery 28.
#   One box: damage 14, trajectory 90 (straight up), BKB 32, KBG 90, WDSK 0.
# Frames/%/angle/BKB/KBG RAW (#120); radius = round(7.81 u × PX_PER_UNIT) = 42 (a wide
# overhead sweep). One box spanning the whole active window (no #204 sub-window). Position
# APPROXIMATED just above the head (small dy) — ⚠🔬 playtest (ADR-0003).
_GNOK_UAIR = MoveData(
    name="up air",
    in_air=True,
    startup=5,
    active=4,
    recovery=28,
    hitboxes=(
        Hitbox(
            circle=Circle(dx=34, dy=4, r=42),
            damage=14.0,
            angle=90,
            base_knockback=32.0,
            knockback_growth=90.0,
        ),
    ),
)


# --- D-air (slices 5-6, #914): DK's AttackAirLw — the SPIKE -------------------
# DK's signature downward stomp: every box launches straight down (angle 270 = meteor). A
# single window with a sweetspot (dmg 16, BKB 38) + two sour boxes (dmg 13, BKB 20).
# Datamined (`-f Donkey -a AttackAirLw`, high_level_frame_data -l subaction; env #614):
#   FAF 42; active frames 18-23 → startup 17 / active 6 / recovery 19.
#   3 boxes, angle 270, KBG 90: id0 dmg 16 BKB 38 (sweetspot), id1/id2 dmg 13 BKB 20 (sour).
# Frames/%/angle/BKB/KBG RAW (#120); radii = round(size u × PX_PER_UNIT): 7.03→38, 6.25→34,
# 4.69→25. One window (no #204 sub-window). Positions APPROXIMATED below the body (large dy —
# a downward stomp), the sweetspot centered under the feet — ⚠🔬 playtest (ADR-0003).
def _dair_box(dx, dy, r, damage, bkb):
    return Hitbox(
        circle=Circle(dx=dx, dy=dy, r=r),
        damage=damage,
        angle=270,
        base_knockback=bkb,
        knockback_growth=90.0,
    )


_GNOK_DAIR = MoveData(
    name="down air",
    in_air=True,
    startup=17,
    active=6,
    recovery=19,
    hitboxes=(
        _dair_box(dx=44, dy=72, r=38, damage=16.0, bkb=38.0),  # sweetspot — the meteor
        _dair_box(dx=28, dy=68, r=34, damage=13.0, bkb=20.0),  # sour (inner)
        _dair_box(dx=58, dy=66, r=25, damage=13.0, bkb=20.0),  # sour (outer)
    ),
)

# --- Smashes (slice 7, #947): DK's chargeable KO tools (AttackS4S/Hi4/Lw4) -----
# The last V1 striking moves. All three are `chargeable=True` — the charge mechanic is
# live (#371/#377, proven by Narz), so no new engine work; the angled f-smash is engine-side
# too (global FSMASH_ANGLE_UP/DOWN applied to any move keyed "fsmash", #383/#327) — no
# per-character angle field. Each is a SINGLE active window (no #204 early/late decay in the
# DK smash data), so — like nalio's usmash/dsmash and narz's fsmash/usmash — no `set_id` is
# needed: the engine already resolves overlapping same-window boxes to one hit per target per
# move, and each side of the two-sided d-smash is a distinct target.
#
# Datamined at DEV time from the brawllib_rs PM3.6 dump (`-f Donkey -a AttackS4S|AttackHi4|
# AttackLw4`, high_level_frame_data -l subaction; env #614). Frames / % / angle / BKB / KBG
# entered RAW (#120). Radii = round(size u × PX_PER_UNIT) as for every other Gnok move.
# Positions dx/dy APPROXIMATED (no skeleton modeled) — ⚠🔬 playtest starting points (ADR-0003).


# Forward-smash (AttackS4S): DK's two-hand forward clap — the heavy KO poke. FOUR same-angle
# boxes (rukaidata id 0→3), all trajectory 361 (Sakurai #203). The two big fists (id0/id1)
# hit hardest (dmg 20/21, BKB 30, KBG 94); the two inner boxes (id2/id3) are the weaker link
# (dmg 19/18, BKB 18, KBG 100). Datamine: IASA 40, active frames 8-9 → startup 7 / active 2 /
# recovery 31. Radii: 5.47→30, 4.69→25, 3.33→18, 2.34→13. Ordered by reach (biggest fist first
# = tuple priority on overlap).
def _fsmash_box(dx, r, damage, bkb, kbg):
    return Hitbox(
        circle=Circle(dx=dx, dy=42, r=r),
        damage=damage,
        angle=361,
        base_knockback=bkb,
        knockback_growth=kbg,
    )


_GNOK_FSMASH = MoveData(
    name="fsmash",
    in_air=False,
    chargeable=True,
    startup=7,  # AttackS4S first active frame 8 (1-indexed) → 7 startup frames
    active=2,  # active frames 8-9
    recovery=31,  # IASA 40 → 40 - 7 - 2 = 31
    hitboxes=(
        _fsmash_box(dx=92, r=30, damage=21.0, bkb=30.0, kbg=94.0),  # id1 (size 5.47) — big fist, furthest
        _fsmash_box(dx=78, r=25, damage=20.0, bkb=30.0, kbg=94.0),  # id0 (size 4.69) — fist
        _fsmash_box(dx=62, r=18, damage=19.0, bkb=18.0, kbg=100.0),  # id2 (size 3.33) — inner link
        _fsmash_box(dx=50, r=13, damage=18.0, bkb=18.0, kbg=100.0),  # id3 (size 2.34) — innermost link
    ),
)


# Up-smash (AttackHi4): a big overhead double-arm clap straight up — the anti-air/juggle KO.
# TWO boxes (rukaidata id 0→1), both trajectory 90 (straight up), BKB 40, KBG 98; the main
# box (id0, dmg 18) is huge, the inner (id1, dmg 16) slightly weaker. Datamine: IASA 41,
# active frames 8-10 → startup 7 / active 3 / recovery 31. Radii: 8.5→46 (a wide overhead
# sweep), 6.25→34. Centered over the 76-wide body (dx ≈ 38).
_GNOK_USMASH = MoveData(
    name="usmash",
    in_air=False,
    chargeable=True,
    startup=7,  # AttackHi4 first active frame 8 (1-indexed) → 7 startup frames
    active=3,  # active frames 8-10
    recovery=31,  # IASA 41 → 41 - 7 - 3 = 31
    hitboxes=(
        Hitbox(
            circle=Circle(dx=38, dy=-6, r=46),
            damage=18.0,
            angle=90,
            base_knockback=40.0,
            knockback_growth=98.0,
        ),  # id0 (size 8.5) — main overhead
        Hitbox(
            circle=Circle(dx=38, dy=14, r=34),
            damage=16.0,
            angle=90,
            base_knockback=40.0,
            knockback_growth=98.0,
        ),  # id1 (size 6.25) — inner
    ),
)


# Down-smash (AttackLw4): DK's two-sided ground pound — hits FRONT and BACK together (a single
# window, unlike Marth/narz's front-then-back split). FOUR boxes, a big pair (id0/id1, dmg 17,
# trajectory 115, r27) and a small pair (id2/id3, dmg 16, trajectory 98, r22), BKB 35, KBG 100,
# both trajectories near-vertical (the move pops opponents up). Placed front (dx>0) + back
# (dx<0); the sim mirror-flips dx with facing and flips the launch x by attacker facing.
# Datamine: IASA 52, active frames 8-11 → startup 7 / active 4 / recovery 41. Radii: 5.0→27,
# 4.0→22. Low along the ground (large dy).
def _dsmash_box(dx, r, damage, angle):
    return Hitbox(
        circle=Circle(dx=dx, dy=66, r=r),
        damage=damage,
        angle=angle,
        base_knockback=35.0,
        knockback_growth=100.0,
    )


_GNOK_DSMASH = MoveData(
    name="dsmash",
    in_air=False,
    chargeable=True,
    startup=7,  # AttackLw4 first active frame 8 (1-indexed) → 7 startup frames
    active=4,  # active frames 8-11
    recovery=41,  # IASA 52 → 52 - 7 - 4 = 41
    hitboxes=(
        _dsmash_box(dx=46, r=27, damage=17.0, angle=115),  # id0 (size 5.0) — front, big
        _dsmash_box(dx=-46, r=27, damage=17.0, angle=115),  # id1 (size 5.0) — back, big
        _dsmash_box(dx=30, r=22, damage=16.0, angle=98),  # id2 (size 4.0) — front, inner
        _dsmash_box(dx=-30, r=22, damage=16.0, angle=98),  # id3 (size 4.0) — back, inner
    ),
)


# --- Idle rest loop (#1105, Decision A #1104) ---------------------------------
# Idle as a first-class MoveData so it flows through the standard move pipeline (editor
# move cycle / timeline / scrubber / reference-GIF layer) like every attack — no bespoke
# idle mechanism. No active hitbox window → empty hitboxes; the posture stand hurtbox
# (_HURTBOX) already covers idle (#1082), so no per-move hurtbox override. Loop length =
# PM DK `Wait1` subaction, brawllib_rs datamine (env #614): 141 frames (FOUND) — the longest
# idle loop of the four cats (DK's heavy, slow sway). Modeled as recovery with startup =
# active = 0.
_WAIT = MoveData(name="wait", in_air=False, startup=0, active=0, recovery=141, hitboxes=())


GNOK_FIGHTER_DATA = FighterData(
    # Own measured big body + 4-circle hurtbox (spec §2); crouch/prone geometry; the faithful
    # PM3.6 velocity scalars authored raw-first via vel() (#785). The full V1 striking kit is
    # now authored — jab (#824), 3 tilts (#841), 5 aerials (#914), 3 smashes (#947); only the
    # dash-attack slot (slice 4) still reuses the default cat until it lands (#779).
    hurtbox=_HURTBOX,
    stand_size=_STAND_SIZE,
    moves={
        **_DEFAULT.moves,
        "jab": _GNOK_JAB,
        "ftilt": _GNOK_FTILT,
        "utilt": _GNOK_UTILT,
        "dtilt": _GNOK_DTILT,
        "nair": _GNOK_NAIR,
        "fair": _GNOK_FAIR,
        "bair": _GNOK_BAIR,
        "uair": _GNOK_UAIR,
        "dair": _GNOK_DAIR,
        "fsmash": _GNOK_FSMASH,
        "usmash": _GNOK_USMASH,
        "dsmash": _GNOK_DSMASH,
        "wait": _WAIT,  # idle rest loop (#1105)
    },
    crouch_size=_CROUCH_SIZE,
    crouch_hurtbox=_CROUCH_HURTBOX,
    prone_size=_PRONE_SIZE,
    prone_hurtbox=_PRONE_HURTBOX,
    # Combat scalars RAW (#120); velocity/accel via vel() (#785) — the faithful PM3.6 rates.
    weight=114,  # heaviest cat — dies latest (only defender term in the KB formula)
    move_speed=vel(1.2),  # 6.48 — fastest-walking cat
    dash_speed=vel(1.8),  # 9.72 — fastest-dashing cat
    jump_vel=-vel(2.8),  # -15.12 — jumps highest (negated: pycats jumps are -y)
    gravity=vel(0.1),  # 0.54 — falls a touch harder than default (0.5)
    max_fall_speed=vel(2.4),  # 12.96 — ≈ default (13)
    # max_jumps 2 == default MAX_JUMPS, left defaulted (matches baseline, like narz).
)

# #1041: stamp dense A,B,C hit-box labels — the baseline labeling for authored
# data — so the shipped JSON carries the real `label`s the editor adopts (#1030).
GNOK_FIGHTER_DATA = with_dense_hit_labels(GNOK_FIGHTER_DATA)
