"""
pycats/characters/nalio_cat.py

Purpose: FighterData for the "Nalio" cat — the balanced all-rounder, first
archetype of the 5-cat Project M epic (#117), specced in #119. Nalio is the
feline character that *plays as* the Project M Mario archetype.

Source: Project M 3.6 Mario (canonical reference, see
docs/research-spec-119-mario-cat-pm.md and docs/research-120-smash-units-and-sources.md).
Unit convention from #120: combat numbers (frames / %, damage, weight, BKB, KBG,
angle) are entered RAW; spatial values scale by PX_PER_UNIT ≈ 5.4 px/unit.

Why Nalio maps so cleanly to PM Mario:
  PM3.6 Mario's weight (100), gravity, jump velocity, walk speed, and jump count
  already match pycats' global defaults at 5.4 px/unit — so the all-rounder feel
  is the baseline pycats already ships. This module pins it as DISTINCT data so
  the other four archetypes have something to diverge from.

Scope of this slice (#123):
  - weight + body/hurtbox geometry + ONE PM-faithful move (down-tilt).
  - Nalio's full moveset (smashes, aerials, specials) is gated on later Phase 2
    slices; per-move claw/fist visuals are #125; crouch is #124.

Jab ("jab") — PM3.6 Mario `Attack11` (rukaidata), first neutral-A slice (#154).
  Total 16f / IASA 16. Hitboxes active frames 2-3, modelled as startup 1 /
  active 2 / recovery 13 in pycats' MoveData window.

  rukaidata reports three same-set hitboxes:

    id  bone  damage  size(u)  -> r px (×5.4)  angle  WDSK  BKB  KBG  x(u)
    0   25    3       3.52     19              83     20    0    100  2.58
    1   22    3       2.34     13              83     20    0    100  1.29
    2   46    3       2.73     15              85     20    0    100  0.00

  WDSK's special knockback formula is not represented in Hitbox yet, so this
  slice records BKB/KBG raw and documents WDSK as deferred. Positions are
  approximated like down-tilt: rukaidata offsets are bone-relative and pycats has
  no Mario skeleton. The fist/primary hitbox is anchored just beyond the body at
  dx=54, with arm/body boxes trailing inward.

Down-tilt ("attack") — PM3.6 Mario `AttackLw3` (rukaidata), real 3-hitbox form
  (#132, on the #130 multi-hitbox engine; replaces #123's single-hit approx).
  Mapped onto the "attack" move slot, so Nalio is usable via the attack button.

  All three hitboxes are active frames 5-8 (simultaneous) and share angle 80
  (low launch — a d-tilt pops the opponent up-and-out), BKB 30, KBG 80. They are
  listed in PRIORITY order (rukaidata hitbox id 0->2; lower id wins on overlap,
  the Smash convention #130 implements):

    id  bone  damage  size(u)  -> r px (×5.4)   along-limb y (u)
    0   10    9       2.34     13               0.0
    1   16    9       3.13     17               1.72
    2   17    8       3.91     21               3.80

  Timing: startup 5 / active 4 / recovery 21 (30f total, interruptible ~28).

  Raw values (damage, angle, BKB, KBG, sizes) are datamined from rukaidata; radii
  = round(size × 5.4) per #120. POSITIONS are a documented approximation: rukaidata
  x/y/z are bone-relative and the skeleton isn't modelled, so (as #119 did for the
  single box) the mid box (id1) is anchored at the #64-validated reach dx=46, and
  the others are spread by the rukaidata along-limb deltas ×5.4 (≈9px, ≈20px) →
  id0 dx=37, id1 dx=46, id2 dx=57; dy=30 (the low d-tilt band) for all. Replacing
  this with a true skeleton→pixel mapping is a later refinement.
"""

from pycats.combat.data import Circle, FighterData, Hitbox, Hurtbox, MoveData

# --- Hurtbox: reuse the 2-circle stack (40×60 body) as a medium-build ---------
# approximation (spec §3: Mario's datamined capsules are a later refinement).
_HURTBOX = Hurtbox(
    circles=(
        Circle(dx=20, dy=15, r=14),   # upper body
        Circle(dx=20, dy=45, r=14),   # lower body
    )
)

# --- Jab, mapped to the canonical "jab" key (PM3.6 Mario Attack11) ------------
# Real 3-hitbox first jab (#154). Active frames 2-3, IASA/total 16. WDSK 20 is
# deferred because Hitbox has no weight-dependent-set-knockback field yet.
_JAB = MoveData(
    name="jab",
    in_air=False,
    startup=1,
    active=2,
    recovery=13,
    hitboxes=(
        Hitbox(circle=Circle(dx=54, dy=27, r=19), damage=3.0,
               angle=83, base_knockback=0.0, knockback_growth=100.0),
        Hitbox(circle=Circle(dx=44, dy=28, r=13), damage=3.0,
               angle=83, base_knockback=0.0, knockback_growth=100.0),
        Hitbox(circle=Circle(dx=34, dy=29, r=15), damage=3.0,
               angle=85, base_knockback=0.0, knockback_growth=100.0),
    ),
)

# --- Down-tilt, mapped to the "attack" slot (PM3.6 Mario AttackLw3) ------------
# Real 3-hitbox form (#132). All active 5-8, angle 80 / BKB 30 / KBG 80; raw
# damage 9/9/8 and radii 13/17/21 (sizes 2.34/3.13/3.91 u × 5.4). Listed in
# priority order (rukaidata id 0->2). dx/dy approximated — see module docstring.
def _dtilt_box(dx, r, damage):
    return Hitbox(circle=Circle(dx=dx, dy=30, r=r), damage=damage,
                  angle=80, base_knockback=30.0, knockback_growth=80.0)

_DOWN_TILT = MoveData(
    name="down tilt",
    in_air=False,
    startup=5,
    active=4,
    recovery=21,
    hitboxes=(
        _dtilt_box(dx=37, r=13, damage=9.0),   # id0 (bone 10) — inner, priority
        _dtilt_box(dx=46, r=17, damage=9.0),   # id1 (bone 16) — mid (#64 reach)
        _dtilt_box(dx=57, r=21, damage=8.0),   # id2 (bone 17) — tip, furthest
    ),
)

# --- Neutral-air, mapped to the "nair" slot (PM3.6 Mario AttackAirN) -----------
# Nalio's first aerial (#136), authored as the CLEAN-HIT form on the #130 engine.
# A "sex kick" — 2 simultaneous hitboxes around the body (rukaidata ids 0 & 1,
# bones 17 / 12 at y ±0.86). Raw: damage 12, BKB 20, KBG 100, size 2.73 u → r15.
# Clean hit is active frames 3-6 (startup 2 / active 4); total 46 → recovery 40.
#
# Deliberate approximations (each precedented; see #120):
#   - angle 45 is a LITERAL PLACEHOLDER for the Sakurai sentinel 361 (a code, not
#     degrees); real Sakurai-angle handling is a deferred #38 slice.
#   - CLEAN HIT ONLY — the real move has a late hit (frames 7-30, 9%), a 2nd
#     temporal window the single-window MoveData can't express yet (#67 gap).
#   - positions are bone-relative → approximated around Nalio's body.
#   - landing lag / auto-cancel / L-cancel are deferred (no landing-lag system).
def _nair_box(dx, dy):
    return Hitbox(circle=Circle(dx=dx, dy=dy, r=15), damage=12.0,
                  angle=45, base_knockback=20.0, knockback_growth=100.0)

_NEUTRAL_AIR = MoveData(
    name="neutral air",
    in_air=True,
    startup=2,
    active=4,
    recovery=40,
    hitboxes=(
        _nair_box(dx=30, dy=24),   # id0 (bone 17) — front/upper
        _nair_box(dx=10, dy=38),   # id1 (bone 12) — back/lower
    ),
)

# --- Crouch geometry (#124) ---------------------------------------------------
# PM Mario's crouch is a moderate lower (not a Kirby-style ground-hug). The body
# Rect resizes from the 40×60 stand box to a squarish 40×40 crouch box (feet
# planted), and the hurtbox swaps to a lower/shorter pair of circles so high
# attacks whiff. Coords are relative to the crouched rect top-left. ⚠ playtest
# starting points (per-cat tuning, like the other archetype numbers).
_CROUCH_SIZE = (40, 40)
_CROUCH_HURTBOX = Hurtbox(
    circles=(
        Circle(dx=20, dy=20, r=14),   # lowered torso
        Circle(dx=20, dy=32, r=12),   # legs (near the planted feet)
    )
)

# --- Assembled FighterData ----------------------------------------------------
NALIO_FIGHTER_DATA = FighterData(
    weight=100,            # PM3.6 Mario (== pycats default → no KB change)
    hurtbox=_HURTBOX,
    moves={"attack": _DOWN_TILT, "jab": _JAB, "nair": _NEUTRAL_AIR},
    crouch_size=_CROUCH_SIZE,
    crouch_hurtbox=_CROUCH_HURTBOX,
)
