"""
pycats/characters/nalio_cat.py

Purpose: FighterData for the "Nalio" cat — the balanced all-rounder, first
archetype of the 5-cat Project M epic (#117), specced in #119. Nalio is the
feline character that *plays as* the Project M Mario archetype.

Source: Project M 3.6 Mario (canonical reference, see
docs/research-spec-119-mario-cat-pm.md and docs/research-120-smash-units-and-sources.md).
Unit convention from #120: combat numbers (frames / %, damage, weight, BKB, KBG,
angle) are entered RAW; spatial values scale by PX_PER_UNIT (config.py, #120).

Why Nalio maps so cleanly to PM Mario:
  PM3.6 Mario's weight (100), gravity, jump velocity, walk speed, and jump count
  already match pycats' global defaults at PX_PER_UNIT px/unit — so the all-rounder feel
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

    id  bone  damage  size(u)  -> r px (×PX_PER_UNIT)  angle  WDSK  BKB  KBG  x(u)
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

    id  bone  damage  size(u)  -> r px (×PX_PER_UNIT)   along-limb y (u)
    0   10    9       2.34     13               0.0
    1   16    9       3.13     17               1.72
    2   17    8       3.91     21               3.80

  Timing: startup 5 / active 4 / recovery 21 (30f total, interruptible ~28).

  Raw values (damage, angle, BKB, KBG, sizes) are datamined from rukaidata; radii
  = round(size × PX_PER_UNIT) per #120. POSITIONS are a documented approximation: rukaidata
  x/y/z are bone-relative and the skeleton isn't modelled, so (as #119 did for the
  single box) the mid box (id1) is anchored at the #64-validated reach dx=46, and
  the others are spread by the rukaidata along-limb deltas ×PX_PER_UNIT (≈9px, ≈20px) →
  id0 dx=37, id1 dx=46, id2 dx=57; dy=30 (the low d-tilt band) for all. Replacing
  this with a true skeleton→pixel mapping is a later refinement.
"""

from pycats.combat.data import Circle, FighterData, Hitbox, Hurtbox, MoveData
from pycats.combat.units import u  # units->px authoring scale (#195)

# --- Hurtbox: reuse the 2-circle stack (40×60 body) as a medium-build ---------
# approximation (spec §3: Mario's datamined capsules are a later refinement).
_HURTBOX = Hurtbox(
    circles=(
        Circle(dx=20, dy=15, r=14),   # upper body
        Circle(dx=20, dy=45, r=14),   # lower body
    )
)

# --- Jab, mapped to the canonical "jab" key (PM3.6 Mario Attack11) ------------
# Real 3-hitbox first jab (#154). Active frames 2-3, IASA/total 16. All three
# hitboxes use SET knockback (rukaidata WDSK 20, BKB 0, KBG 100) — now represented
# via set_knockback (#211/#212), replacing the earlier deferred approximation.
_JAB = MoveData(
    name="jab",
    in_air=False,
    startup=1,
    active=2,
    recovery=13,
    hitboxes=(
        Hitbox(circle=Circle(dx=54, dy=27, r=19), damage=3.0, angle=83,
               base_knockback=0.0, knockback_growth=100.0, set_knockback=20),
        Hitbox(circle=Circle(dx=44, dy=28, r=13), damage=3.0, angle=83,
               base_knockback=0.0, knockback_growth=100.0, set_knockback=20),
        Hitbox(circle=Circle(dx=34, dy=29, r=15), damage=3.0, angle=85,
               base_knockback=0.0, knockback_growth=100.0, set_knockback=20),
    ),
)

# --- Down-tilt, mapped to the "attack" slot (PM3.6 Mario AttackLw3) ------------
# Real 3-hitbox form (#132). All active 5-8, angle 80 / BKB 30 / KBG 80; raw
# damage 9/9/8 and radii 13/17/21 (sizes 2.34/3.13/3.91 u × PX_PER_UNIT). Listed in
# priority order (rukaidata id 0->2). dx/dy approximated — see module docstring.
# NB (#212): verified against rukaidata AttackLw3 — d-tilt uses NORMAL knockback
# (WDSK 0, BKB 30), so it is already faithful; no set_knockback (#211) applies.
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

# --- Forward-tilt, mapped to the canonical "ftilt" key (PM3.6 Mario AttackS3) --
# Forward/mid angle variant (move_select has one ground forward key, so the
# angled up/down variants aren't authored). The FIRST Nalio move to use the real
# Sakurai-angle sentinel 361 (#203) — no literal-angle placeholder needed.
# rukaidata AttackS3 (forward): active 5-7 -> startup 4 / active 3; FAF 30 ->
# recovery 23. Three same-set hitboxes (priority id 0->2), all damage 9, angle
# 361, BKB 6, KBG 100, WDSK 0 (so nothing deferred). Radii = round(size u × PX_PER_UNIT):
# 3.91->21, 3.13->17, 2.73->15. Positions approximated like jab/d-tilt (bones not
# modelled): along the forward arm at mid-body height (dy 28), mid box at the
# #64-validated reach dx=46, fist (id0, r21) outermost.
def _ftilt_box(dx, r):
    return Hitbox(circle=Circle(dx=dx, dy=28, r=r), damage=9.0,
                  angle=361, base_knockback=6.0, knockback_growth=100.0)

_FORWARD_TILT = MoveData(
    name="forward tilt",
    in_air=False,
    startup=4,
    active=3,
    recovery=23,
    hitboxes=(
        _ftilt_box(dx=57, r=21),   # id0 (fist) — outermost, priority
        _ftilt_box(dx=46, r=17),   # id1 — mid (#64 reach)
        _ftilt_box(dx=37, r=15),   # id2 — inner
    ),
)

# --- Up-tilt, mapped to the canonical "utilt" key (PM3.6 Mario AttackHi3) -------
# rukaidata AttackHi3: active 5-11 -> startup 4 / active 7; IASA 30 -> recovery 19.
# Three same-set hitboxes (priority id 0->2), all damage 8, angle 96 (literal —
# an up-and-slightly-back arc, NOT a sentinel), BKB 26, WDSK 0. KBG differs per
# box (125/122/120), recorded faithfully. Radii = round(size u × PX_PER_UNIT): 2.73->15,
# 3.52->19, 4.69->25. Positions approximated (bones not modelled): an overhead arc
# clustered above the head (small dy), id2 (r25) the big sweep behind. Same
# approximation convention as jab/d-tilt/f-tilt.
def _utilt_box(dx, dy, r, kbg):
    return Hitbox(circle=Circle(dx=dx, dy=dy, r=r), damage=8.0,
                  angle=96, base_knockback=26.0, knockback_growth=kbg)

_UP_TILT = MoveData(
    name="up tilt",
    in_air=False,
    startup=4,
    active=7,
    recovery=19,
    hitboxes=(
        _utilt_box(dx=32, dy=8, r=15, kbg=125.0),  # id0 (bone 38) — front, priority
        _utilt_box(dx=22, dy=2, r=19, kbg=122.0),  # id1 (bone 47) — over the head
        _utilt_box(dx=14, dy=6, r=25, kbg=120.0),  # id2 (bone 47) — big sweep, back
    ),
)

# --- Forward-air, mapped to the canonical "fair" key (PM3.6 Mario AttackAirF) ---
# The FIRST move to use the #204 per-hitbox temporal windows: a two-stage f-air,
# the classic Mario forward air. rukaidata AttackAirF: active 16-22 -> startup 15
# / active 7; IASA 45 -> recovery 23. Two windows (MoveClock frame coords):
#   - EARLY [16,17]: angle 60 (up-forward), strong — id0 dmg17/BKB50, id1 dmg16/
#     BKB40, both KBG 100; radii 17/24 (sizes 3.13/4.49 u × PX_PER_UNIT).
#   - LATE  [18,22]: angle 280 (down-and-forward — the METEOR/spike), both dmg15 /
#     BKB30 / KBG70; radii 17/21 (sizes 3.13/3.91 u × PX_PER_UNIT).
# All WDSK 0; angles literal (280 launches downward via the existing code, no
# sentinel). Positions approximated (no skeleton): in front of the body, the late
# meteor boxes swung lower. Landing-lag / auto-cancel / L-cancel deferred (no
# landing-lag system — same as n-air).
def _fair_early(dx, dy, r, damage, bkb):
    return Hitbox(circle=Circle(dx=dx, dy=dy, r=r), damage=damage, angle=60,
                  base_knockback=bkb, knockback_growth=100.0,
                  active_start=16, active_end=17)

def _fair_late(dx, dy, r):
    return Hitbox(circle=Circle(dx=dx, dy=dy, r=r), damage=15.0, angle=280,
                  base_knockback=30.0, knockback_growth=70.0,
                  active_start=18, active_end=22)

_FORWARD_AIR = MoveData(
    name="forward air",
    in_air=True,
    startup=15,
    active=7,
    recovery=23,
    hitboxes=(
        _fair_early(dx=42, dy=18, r=17, damage=17.0, bkb=50.0),  # early id0
        _fair_early(dx=48, dy=26, r=24, damage=16.0, bkb=40.0),  # early id1 (big arc)
        _fair_late(dx=46, dy=36, r=17),                          # late id0 (meteor)
        _fair_late(dx=50, dy=44, r=21),                          # late id1 (spike tip)
    ),
)

# --- Back-air, mapped to the canonical "bair" key (PM3.6 Mario AttackAirB) ------
# A clean->late "sex kick" that consumes BOTH gates: the late hit uses the Sakurai
# sentinel 361 (#203) and the two stages use temporal windows (#204). rukaidata
# AttackAirB: active 6-17 -> startup 5 / active 12; IASA 29 -> recovery 12.
#   - CLEAN [6,8]:  angle 28 (literal), both dmg 11 / BKB 43 / KBG 65; r 25/19.
#   - LATE  [9,17]: angle 361 (Sakurai), both dmg 9 / BKB 20 / KBG 100; r 25/19.
# All WDSK 0. Radii = round(size u × PX_PER_UNIT): 4.69->25, 3.52->19. Positions
# approximated BEHIND the body (negative dx — facing-right-relative; b-air hits
# backward), same x/y for clean and late (same bones 16/17). Landing-lag/L-cancel
# deferred (no landing-lag system — as n-air/f-air).
def _bair_clean(dx, dy, r):
    return Hitbox(circle=Circle(dx=dx, dy=dy, r=r), damage=11.0, angle=28,
                  base_knockback=43.0, knockback_growth=65.0,
                  active_start=6, active_end=8)

def _bair_late(dx, dy, r):
    return Hitbox(circle=Circle(dx=dx, dy=dy, r=r), damage=9.0, angle=361,
                  base_knockback=20.0, knockback_growth=100.0,
                  active_start=9, active_end=17)

_BACK_AIR = MoveData(
    name="back air",
    in_air=True,
    startup=5,
    active=12,
    recovery=12,
    hitboxes=(
        _bair_clean(dx=-12, dy=30, r=25),   # clean id0 (bone 16)
        _bair_clean(dx=-2, dy=34, r=19),    # clean id1 (bone 17)
        _bair_late(dx=-12, dy=30, r=25),    # late id0 (bone 16) — Sakurai
        _bair_late(dx=-2, dy=34, r=19),     # late id1 (bone 17) — Sakurai
    ),
)

# --- Up-air, mapped to the canonical "uair" key (PM3.6 Mario AttackAirHi) -------
# A two-window upward juggle (#204). rukaidata AttackAirHi: active 4-9 -> startup 3
# / active 6; IASA 28 -> recovery 19. Both windows angle 55 (up-and-forward flip),
# BKB 0 (pure-growth — a combo/juggle tool), KBG 100; they differ only in damage:
#   - CLEAN [4,5]: dmg 11.   - LATE [6,9]: dmg 10.
# All WDSK 0. Radii = round(size u × PX_PER_UNIT): 3.52->19, 4.69->25. Positions
# approximated above the head (small dy), same x/y for clean and late (bones
# 16/17). Landing-lag/L-cancel deferred (no system — as the other aerials).
def _uair_box(dx, dy, r, damage, start, end):
    return Hitbox(circle=Circle(dx=dx, dy=dy, r=r), damage=damage, angle=55,
                  base_knockback=0.0, knockback_growth=100.0,
                  active_start=start, active_end=end)

_UP_AIR = MoveData(
    name="up air",
    in_air=True,
    startup=3,
    active=6,
    recovery=19,
    hitboxes=(
        _uair_box(dx=22, dy=4, r=19, damage=11.0, start=4, end=5),   # clean id0
        _uair_box(dx=14, dy=8, r=25, damage=11.0, start=4, end=5),   # clean id1 (big)
        _uair_box(dx=22, dy=4, r=19, damage=10.0, start=6, end=9),   # late id0
        _uair_box(dx=14, dy=8, r=25, damage=10.0, start=6, end=9),   # late id1 (big)
    ),
)

# --- Down-air, mapped to the canonical "dair" key (PM3.6 Mario AttackAirLw) -----
# The looping DRILL — the final move of Nalio's kit, and the one that composes ALL
# THREE Phase-2 gates: #204 temporal windows (the two damage phases), #213
# rehit_rate (the loop within each phase), #211 WDSK (every hit is a set-knockback
# launch). rukaidata AttackAirLw: active 7-27 -> startup 6 / active 21; IASA 35 ->
# recovery 8. All hits angle 85, BKB 0, set knockback (WDSK).
#   - PHASE 1 [7,15]:  dmg 3, WDSK 55, KBG 160.
#   - PHASE 2 [16,27]: dmg 2, WDSK 30, KBG 100.
# rukaidata lists 4 phase-1 / 2 phase-2 boxes at one spot with descending WDSK;
# pycats picks the FIRST overlapping box (priority), so each phase is modelled by
# its priority box (the rest are redundant under first-box-wins). Radii ~5.0 u ×
# PX_PER_UNIT -> 27. Positions approximated BELOW the body (downward drill). rehit_rate=4
# is a ⚠ playtest starting point (the per-hitbox rehit parameter isn't in the basic
# table). Landing-lag/L-cancel deferred (no system — as the other aerials).
def _dair_box(damage, sk, kbg, start, end, dy):
    return Hitbox(circle=Circle(dx=20, dy=dy, r=27), damage=damage, angle=85,
                  base_knockback=0.0, knockback_growth=kbg,
                  set_knockback=sk, active_start=start, active_end=end)

_DOWN_AIR = MoveData(
    name="down air",
    in_air=True,
    startup=6,
    active=21,
    recovery=8,
    rehit_rate=4,   # looping drill cadence (⚠ playtest start)
    hitboxes=(
        _dair_box(damage=3.0, sk=55, kbg=160.0, start=7, end=15, dy=56),   # phase 1
        _dair_box(damage=2.0, sk=30, kbg=100.0, start=16, end=27, dy=58),  # phase 2
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

# --- Neutral-B Fireball (#223, PM3.6 Mario SpecialN) --------------------------
# First special: a flat-travelling projectile (scoped in #155,
# docs/research/nalio-fireball-scoping-findings.md). FOUND values (Smashboards 3.6
# / SmashWiki): throw startup 14, total ~48 (IASA 41 → recovery 33); the projectile
# article lives ~73 frames, 7% damage, Sakurai angle 361 (#203/#206), BKB 22 / KBG
# 20, size 3.5u → r≈19px (×PX_PER_UNIT). active=1 so a single projectile spawns.
# ⚠ projectile_speed is a GUESS (px/frame) — derive via rukaidata units/frame × PX_PER_UNIT
# or playtest (tracked the #192 way). Bounce arc / reflect-absorb are out of scope.
_FIREBALL = MoveData(
    name="fireball",
    in_air=False,
    startup=14,
    active=1,
    recovery=33,
    hitboxes=(
        Hitbox(circle=Circle(dx=50, dy=30, r=u(3.5)), damage=7.0, angle=361,  # 3.5u -> 19px
               base_knockback=22.0, knockback_growth=20.0),
    ),
    projectile_speed=10,     # ⚠ GUESS px/frame (#192/#195 derivation pending)
    projectile_lifetime=73,
)

# --- Smash attacks (uncharged; #327 slice 2) ----------------------------------
# Authored from PM3.6 Mario rukaidata, same convention as the tilts/aerials: raw
# damage/angle/BKB/KBG/frames, radii = u(size), positions the documented
# bones-not-modelled approximation. These are the UNCHARGED release swings, fired
# like a strong tilt via the smash input+routing (#331); the hold-to-charge
# scaling is slice 3 (#327). Sourcing recorded per move below.

# Forward smash — PM3.6 Mario AttackS4S (rukaidata). Active 8-12 -> startup 7 /
# active 5; IASA 38 -> recovery 26. Three same-window boxes (priority id0->2), all
# angle 361 (Sakurai sentinel, #203), WDSK 0: id0 dmg14/BKB25/KBG96 r19 (3.52u),
# id1 dmg19/BKB30/KBG97 r21 (3.94u — the flame sweetspot; the elemental effect
# isn't modelled, only its damage/KB), id2 dmg10/BKB25/KBG96 r11 (1.95u). Positions
# approximated along the forward arm at mid-body height (dy 28, like f-tilt): id0
# (fist) outermost, id1 mid sweetspot, id2 inner.
_FSMASH = MoveData(
    name="forward smash",
    in_air=False,
    startup=7,
    active=5,
    recovery=26,
    hitboxes=(
        Hitbox(circle=Circle(dx=57, dy=28, r=u(3.52)), damage=14.0, angle=361,
               base_knockback=25.0, knockback_growth=96.0),   # id0 fist (priority)
        Hitbox(circle=Circle(dx=47, dy=28, r=u(3.94)), damage=19.0, angle=361,
               base_knockback=30.0, knockback_growth=97.0),   # id1 sweetspot
        Hitbox(circle=Circle(dx=36, dy=28, r=u(1.95)), damage=10.0, angle=361,
               base_knockback=25.0, knockback_growth=96.0),   # id2 inner
    ),
)

# Up smash — PM3.6 Mario AttackHi4 (rukaidata). Active 3-6 -> startup 2 / active 4.
# rukaidata's subaction page doesn't surface IASA/FAF; PM Mario u-smash is
# Melee-faithful FAF 39 -> recovery 33 (⚠ playtest — community frame data, not on
# the rukaidata script). Two windows (#204), all size 3.52u -> r19, WDSK 0:
#   - UP-HIT [3,4]: angle 83 (up, slightly forward), dmg15 / BKB32 / KBG97.
#   - LATE   [5,6]: angle 259 (a down-angled late hit, per rukaidata; ⚠ playtest),
#     dmg16 / BKB35 / KBG95.
# (rukaidata's frame grouping is ambiguous between an up-hit [3,4] and [3,6]; the
# non-overlapping [3,4]/[5,6] split is modelled, matching the two-stage f-air/b-air
# convention.) Positions approximated overhead (like u-tilt): up boxes above the
# head, late boxes slightly lower/forward.
def _usmash_up(dx, dy):
    return Hitbox(circle=Circle(dx=dx, dy=dy, r=u(3.52)), damage=15.0, angle=83,
                  base_knockback=32.0, knockback_growth=97.0,
                  active_start=3, active_end=4)

def _usmash_late(dx, dy):
    return Hitbox(circle=Circle(dx=dx, dy=dy, r=u(3.52)), damage=16.0, angle=259,
                  base_knockback=35.0, knockback_growth=95.0,
                  active_start=5, active_end=6)

_USMASH = MoveData(
    name="up smash",
    in_air=False,
    startup=2,
    active=4,
    recovery=33,
    hitboxes=(
        _usmash_up(dx=2, dy=2),      # id0 over the head
        _usmash_up(dx=12, dy=4),     # id1 front of the head
        _usmash_late(dx=10, dy=12),  # id2 late, lower-forward
        _usmash_late(dx=0, dy=12),   # id3 late, lower
    ),
)

# Down smash — PM3.6 Mario AttackLw4 (rukaidata). A two-hit sweep, front then back;
# active 3-4 (front) + 12-13 (back) -> startup 2 / active 11 (spanning both
# windows); total 36 -> recovery 23. All angle 361 (Sakurai), WDSK 0. Two windows
# (#204): FRONT [3,4] both BKB45/KBG75 — id0 dmg16 r21 (3.91u), id1 dmg16 r17
# (3.13u); BACK [12,13] both BKB40/KBG75 — id0 dmg12 r21, id1 dmg10 r17. Positions
# approximated at ground level (low dy): front boxes ahead (+dx), back behind (-dx,
# facing-right-relative).
def _dsmash_front(dx, r, dmg):
    return Hitbox(circle=Circle(dx=dx, dy=48, r=r), damage=dmg, angle=361,
                  base_knockback=45.0, knockback_growth=75.0,
                  active_start=3, active_end=4)

def _dsmash_back(dx, r, dmg):
    return Hitbox(circle=Circle(dx=dx, dy=48, r=r), damage=dmg, angle=361,
                  base_knockback=40.0, knockback_growth=75.0,
                  active_start=12, active_end=13)

_DSMASH = MoveData(
    name="down smash",
    in_air=False,
    startup=2,
    active=11,
    recovery=23,
    hitboxes=(
        _dsmash_front(dx=40, r=u(3.91), dmg=16.0),   # front id0 (outer)
        _dsmash_front(dx=24, r=u(3.13), dmg=16.0),   # front id1 (inner)
        _dsmash_back(dx=-40, r=u(3.91), dmg=12.0),   # back id0 (outer)
        _dsmash_back(dx=-24, r=u(3.13), dmg=10.0),   # back id1 (inner)
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

# --- Prone geometry (#173) ----------------------------------------------------
# Knocked down, Nalio lies flat — lower than the crouch (40×40) to a short 40×22
# box, feet planted, with a low/flat hurtbox so high attacks whiff over the downed
# fighter. ⚠ playtest starting points (per-cat tuning, like the crouch numbers).
_PRONE_SIZE = (40, 22)
_PRONE_HURTBOX = Hurtbox(
    circles=(
        Circle(dx=18, dy=12, r=11),   # torso, lying low
        Circle(dx=26, dy=14, r=9),    # legs along the ground
    )
)

# --- Assembled FighterData ----------------------------------------------------
NALIO_FIGHTER_DATA = FighterData(
    weight=100,            # PM3.6 Mario (== pycats default → no KB change)
    hurtbox=_HURTBOX,
    moves={"attack": _DOWN_TILT, "jab": _JAB, "ftilt": _FORWARD_TILT,
           "utilt": _UP_TILT, "fair": _FORWARD_AIR, "bair": _BACK_AIR,
           "uair": _UP_AIR, "dair": _DOWN_AIR, "nair": _NEUTRAL_AIR,
           "neutral_b": _FIREBALL,
           "fsmash": _FSMASH, "usmash": _USMASH, "dsmash": _DSMASH},
    crouch_size=_CROUCH_SIZE,
    crouch_hurtbox=_CROUCH_HURTBOX,
    prone_size=_PRONE_SIZE,
    prone_hurtbox=_PRONE_HURTBOX,
)
