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
windows. Slice 3 (#841) adds the three **tilts** — f-tilt (`AttackS3S`), u-tilt (`AttackHi3`),
d-tilt (`AttackLw3`); the rest of `moves` still reuses the default cat until its slice lands.
Gnok's remaining heavy normals + smashes arrive one slice at a time under #779 (slices 4-7).
Deferred (NOT V1, need engine): grabs/throws, Giant Punch armor, Spinning Kong recovery
(spec §3/§5).

Faithful-physics caveat (#785/#816): pycats' shipped velocity globals are *game-tuned px*,
not rukaidata × 5.4 (e.g. MAX_FALL_SPEED = 13 vs Mario's real ~9.2). Gnok's `vel()` values
are the faithful PM3.6 rates; a roster-wide faithful re-tune is deferred to #816. Gnok does
not block on it — it ships on the same basis the other cats do, just authored via the seam.
"""

from pycats.characters.default_cat import DEFAULT_FIGHTER_DATA as _DEFAULT
from pycats.combat.data import Circle, FighterData, Hitbox, Hurtbox, MoveData
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

GNOK_FIGHTER_DATA = FighterData(
    # Own measured big body + 4-circle hurtbox (spec §2); crouch/prone geometry; the faithful
    # PM3.6 velocity scalars authored raw-first via vel() (#785). Slice 2 (#824) adds the
    # jab (DK's 1-2); the other slots reuse the default cat until their slices (#779) land.
    hurtbox=_HURTBOX,
    stand_size=_STAND_SIZE,
    moves={
        **_DEFAULT.moves,
        "jab": _GNOK_JAB,
        "ftilt": _GNOK_FTILT,
        "utilt": _GNOK_UTILT,
        "dtilt": _GNOK_DTILT,
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
