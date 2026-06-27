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
  - Nalio's full moveset (jab multi-hit, smashes, aerials, specials) is gated on
    the combat core #38; per-move claw/fist visuals are #125; crouch is #124.

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

# --- Assembled FighterData ----------------------------------------------------
NALIO_FIGHTER_DATA = FighterData(
    weight=100,            # PM3.6 Mario (== pycats default → no KB change)
    hurtbox=_HURTBOX,
    moves={"attack": _DOWN_TILT},
)
