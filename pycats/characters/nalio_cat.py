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

Down-tilt ("attack") — PM3.6 Mario `AttackLw3` (rukaidata):
  Mapped onto the single "attack" move slot pycats supports today, so Nalio is
  immediately usable via the attack button (the generic jab placeholder is what
  this replaces *for Nalio only* — the default cat keeps its own).
    damage   = 9    (raw; single-hit approximation of PM's 3-hitbox d-tilt)
    BKB      = 30   (raw)
    KBG      = 80   (raw)
    angle    = 80°  (raw; low launch — a d-tilt pops the opponent up-and-out)
    startup  = 5    (PM active frames 5-8)
    active   = 4    (frames 5-8 inclusive)
    recovery = 21   (30-frame total move, interruptible ~frame 28)
    hitbox r = 17px (PM 2.34-3.91 units × 5.4; single circle approximates the set)
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
_DOWN_TILT_HITBOX = Hitbox(
    circle=Circle(dx=46, dy=30, r=17),
    damage=9.0,
    angle=80,
    base_knockback=30.0,
    knockback_growth=80.0,
)

_DOWN_TILT = MoveData(
    name="down tilt",
    in_air=False,
    startup=5,
    active=4,
    recovery=21,
    hitboxes=(_DOWN_TILT_HITBOX,),
)

# --- Assembled FighterData ----------------------------------------------------
NALIO_FIGHTER_DATA = FighterData(
    weight=100,            # PM3.6 Mario (== pycats default → no KB change)
    hurtbox=_HURTBOX,
    moves={"attack": _DOWN_TILT},
)
