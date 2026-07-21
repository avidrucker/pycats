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

This slice authors **no moves** — `moves` reuses the default cat (like narz_cat.py slice 1),
so Gnok differs from the default in scalars + body geometry only. Gnok's heavy normals +
smashes arrive one slice at a time under #779 (slices 2-7). Deferred (NOT V1, need engine):
grabs/throws, Giant Punch armor, Spinning Kong recovery (spec §3/§5).

Faithful-physics caveat (#785/#816): pycats' shipped velocity globals are *game-tuned px*,
not rukaidata × 5.4 (e.g. MAX_FALL_SPEED = 13 vs Mario's real ~9.2). Gnok's `vel()` values
are the faithful PM3.6 rates; a roster-wide faithful re-tune is deferred to #816. Gnok does
not block on it — it ships on the same basis the other cats do, just authored via the seam.
"""

from pycats.characters.default_cat import DEFAULT_FIGHTER_DATA as _DEFAULT
from pycats.combat.data import Circle, FighterData, Hurtbox
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

GNOK_FIGHTER_DATA = FighterData(
    # Own measured big body + 4-circle hurtbox (spec §2); crouch/prone geometry; the faithful
    # PM3.6 velocity scalars authored raw-first via vel() (#785). No moves this slice — the
    # default cat's "attack" is the neutral-A fallback until slices 2-7 (#779) add Gnok's kit.
    hurtbox=_HURTBOX,
    stand_size=_STAND_SIZE,
    moves=dict(_DEFAULT.moves),
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
