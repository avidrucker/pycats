"""FighterData for "Narz" — the Marth archetype (disjointed swordfighter). Slice 1 of #294.

Narz's *mobility* is near-Mario (#290 finding): only the **weight** and a slightly
**floatier gravity** (plus a touch lower jump velocity) differ from the default/Mario
baseline. The archetype identity is NOT in these scalars — it is in **move geometry**
(disjoint reach + tipper), which slice 2 (the forward-tilt) introduces.

Values from the #290 scoping spec (PM3.6 Marth; ⚠ playtest / rukaidata-confirm later):

    weight 87 · gravity 0.45 · jump_vel -12   (deltas)
    max_jumps 2 · move_speed 6 · max_fall_speed 13   (= baseline, left as defaults)

Per #120, these scalars are entered RAW (the ×PX_PER_UNIT unit scale is for *spatial* values).

This slice authors **no moves** — `hurtbox`, `moves`, and crouch/prone geometry reuse the
default cat as placeholders, so Narz differs from the default *only* in the three scalars.
Narz's disjoint/tipper moves arrive one slice at a time under #294.
"""
from pycats.characters.default_cat import DEFAULT_FIGHTER_DATA as _DEFAULT
from pycats.combat.data import Circle, FighterData, Hitbox, MoveData

# --- Forward-tilt (slice 2, #299): the disjoint+tipper IDENTITY move --------------
# Narz's signature: a sword poke that reaches BEYOND the hurtbox (disjoint) and rewards
# spacing (tipper — the far tip hits harder than the near base). Both are pure data on
# the current engine (#290): the tip box is FIRST in the tuple, so when a defender
# overlaps both, priority = tuple order (attack.py:36; combat.py:141) makes the tip win.
#
# PM3.6 Marth `AttackS3` (forward-tilt), ⚠ playtest / rukaidata-confirm later. #120 units:
# frames / % / angle / BKB / KBG entered RAW; radii are px (the blade is thin → small r).
# The default hurtbox spans dx 6..34; the tip sits at dx 60..84 — wholly disjoint.
_NARZ_FTILT = MoveData(
    name="ftilt",
    in_air=False,
    startup=6,
    active=3,
    recovery=21,  # 6 + 3 + 21 = 30 (PM3.6 total / IASA)
    hitboxes=(
        # TIP (box 0, highest priority): far + strong — the spacing/KO hit.
        Hitbox(circle=Circle(dx=72, dy=30, r=12), damage=13.0, angle=361,
               base_knockback=30.0, knockback_growth=80.0),
        # BASE (box 1): near the body + weak — the punished close hit.
        Hitbox(circle=Circle(dx=48, dy=30, r=14), damage=10.0, angle=361,
               base_knockback=18.0, knockback_growth=55.0),
    ),
)

# --- Jab (slice 3, #301): a fast, disjoint neutral-A poke -------------------------
# Marth's jab (PM3.6 `Attack11`) is a quick sword stab — ONE box (not a tipper; that's
# the f-tilt). It still reaches past the hurtbox (disjoint), but closer + weaker than
# the f-tilt tip, and much faster (startup 4 vs 6). ⚠ playtest / rukaidata-confirm.
# #120 units: frames/%/angle/BKB/KBG RAW; the thin blade → small r. The default hurtbox
# spans dx 6..34; this box sits at dx 48..68 — disjoint.
_NARZ_JAB = MoveData(
    name="jab",
    in_air=False,
    startup=4,
    active=2,
    recovery=8,  # 4 + 2 + 8 = 14 (fast poke)
    hitboxes=(
        Hitbox(circle=Circle(dx=58, dy=28, r=10), damage=4.0, angle=361,
               base_knockback=15.0, knockback_growth=30.0),
    ),
)

# --- Down-tilt (slice 4, #303): a low, disjoint, tippered edgeguard poke ----------
# Marth's low spacing tool: the same 2-box tipper shape as the f-tilt (tip box FIRST,
# stronger; priority = tuple order, attack.py:36 / combat.py:141), but near the feet
# (high dy) and at a LOW launch angle (sends low/outward — the edgeguard / 2-frame use),
# unlike the f-tilt's 361 sentinel. PM3.6 Marth `AttackLw3`, ⚠ playtest / rukaidata-confirm.
# Tip at dx 56..76 (disjoint past the hurtbox 6..34).
_NARZ_DTILT = MoveData(
    name="dtilt",
    in_air=False,
    startup=5,
    active=2,
    recovery=13,  # 5 + 2 + 13 = 20
    hitboxes=(
        # TIP (box 0): far + low + strong.
        Hitbox(circle=Circle(dx=66, dy=46, r=10), damage=9.0, angle=30,
               base_knockback=20.0, knockback_growth=70.0),
        # BASE (box 1): near + low + weak.
        Hitbox(circle=Circle(dx=44, dy=48, r=12), damage=7.0, angle=30,
               base_knockback=12.0, knockback_growth=50.0),
    ),
)

# --- Up-tilt (slice 5, #305): an anti-air, disjoint, tippered overhead arc ---------
# Marth's anti-air: the 2-box tipper shape (tip box FIRST, stronger; priority = tuple
# order) hitting ABOVE the head (negative/low dy) and sending UP (angle ~90 — the
# juggle use), distinct from the f-tilt (forward 361) and d-tilt (low 30). The disjoint
# here is VERTICAL — the tip reaches above the hurtbox top. PM3.6 Marth `AttackHi3`,
# ⚠ playtest / rukaidata-confirm. Completes the #294 ground normals.
_NARZ_UTILT = MoveData(
    name="utilt",
    in_air=False,
    startup=6,
    active=3,
    recovery=14,  # 6 + 3 + 14 = 23
    hitboxes=(
        # TIP (box 0): above the head + strong.
        Hitbox(circle=Circle(dx=24, dy=-8, r=14), damage=12.0, angle=90,
               base_knockback=25.0, knockback_growth=80.0),
        # BASE (box 1): head level + weak.
        Hitbox(circle=Circle(dx=24, dy=8, r=12), damage=9.0, angle=90,
               base_knockback=18.0, knockback_growth=60.0),
    ),
)

# --- Neutral-air (slice 6, #307): the first sword AERIAL, a disjoint tipper swipe ---
# Narz's first in_air move (the air/ground split, #38): the 2-box tipper shape (tip box
# FIRST, stronger; priority = tuple order) as an aerial sword swipe around the body,
# reaching past the hurtbox (disjoint). PM3.6 Marth `AttackAirN`, ⚠ playtest / rukaidata-
# confirm. Tip at dx 48..72 (disjoint past the hurtbox 6..34).
_NARZ_NAIR = MoveData(
    name="nair",
    in_air=True,
    startup=4,
    active=4,
    recovery=12,  # 4 + 4 + 12 = 20
    hitboxes=(
        # TIP (box 0): far + strong.
        Hitbox(circle=Circle(dx=60, dy=30, r=12), damage=11.0, angle=45,
               base_knockback=15.0, knockback_growth=90.0),
        # BASE (box 1): near + weak.
        Hitbox(circle=Circle(dx=40, dy=30, r=14), damage=8.0, angle=45,
               base_knockback=10.0, knockback_growth=70.0),
    ),
)

# --- Forward-air (slice 7, #313): the ICONIC spacing wall — longest disjoint tipper --
# The move that most defines the Marth archetype: a forward aerial sword swipe with the
# LONGEST disjoint reach of the kit (tip at dx 58..82, farther than the n-air's 48..72).
# The 2-box tipper shape (tip box FIRST, stronger; priority = tuple order) rewards spacing
# the very end of the blade. PM3.6 Marth `AttackAirF`, ⚠ playtest / rukaidata-confirm.
_NARZ_FAIR = MoveData(
    name="fair",
    in_air=True,
    startup=5,
    active=3,
    recovery=16,  # 5 + 3 + 16 = 24
    hitboxes=(
        # TIP (box 0): farthest + strongest — the spacing wall.
        Hitbox(circle=Circle(dx=70, dy=28, r=12), damage=12.0, angle=45,
               base_knockback=15.0, knockback_growth=95.0),
        # BASE (box 1): nearer + weaker.
        Hitbox(circle=Circle(dx=46, dy=30, r=14), damage=9.0, angle=45,
               base_knockback=10.0, knockback_growth=75.0),
    ),
)

# --- Back-air (slice 8, #316): a strong disjoint tipper BEHIND the body -------------
# Marth's backward KO/spacing poke: the 2-box tipper shape (tip box FIRST, stronger;
# priority = tuple order) authored with NEGATIVE dx so it swings behind a right-facing
# fighter (mirrored for left by the consumers). The tip is the strongest aerial tip so
# far (a KO hit). PM3.6 Marth `AttackAirB`, ⚠ playtest / rukaidata-confirm. Tip at
# dx -76..-52 — wholly behind the hurtbox (back edge dx 6).
_NARZ_BAIR = MoveData(
    name="bair",
    in_air=True,
    startup=5,
    active=3,
    recovery=15,  # 5 + 3 + 15 = 23
    hitboxes=(
        # TIP (box 0): farthest-behind + strongest (the KO tip).
        Hitbox(circle=Circle(dx=-64, dy=28, r=12), damage=13.0, angle=45,
               base_knockback=18.0, knockback_growth=90.0),
        # BASE (box 1): nearer-behind + weaker.
        Hitbox(circle=Circle(dx=-42, dy=30, r=14), damage=9.0, angle=45,
               base_knockback=10.0, knockback_growth=70.0),
    ),
)

# --- Up-air (slice 9, #323): an overhead juggle arc, disjoint tipper ----------------
# Marth's juggle aerial: the up-tilt's vertical disjoint as an aerial — the 2-box tipper
# (tip box FIRST, stronger; priority = tuple order) hitting ABOVE the fighter (tip dy=-10)
# and sending UP (angle 90). The tip's top edge (dy-r=-24) clears the hurtbox top (dy 1).
# PM3.6 Marth `AttackAirHi`, ⚠ playtest / rukaidata-confirm.
_NARZ_UAIR = MoveData(
    name="uair",
    in_air=True,
    startup=5,
    active=3,
    recovery=14,  # 5 + 3 + 14 = 22
    hitboxes=(
        # TIP (box 0): above + strong.
        Hitbox(circle=Circle(dx=22, dy=-10, r=14), damage=12.0, angle=90,
               base_knockback=20.0, knockback_growth=90.0),
        # BASE (box 1): head level + weak.
        Hitbox(circle=Circle(dx=22, dy=8, r=12), damage=9.0, angle=90,
               base_knockback=12.0, knockback_growth=70.0),
    ),
)

# --- Down-air (slice 10, #324): a meteor spike below the fighter --------------------
# Marth's meteor: the 2-box tipper shape (tip box FIRST, stronger; priority = tuple order)
# below the body (high dy) with a straight-DOWN spike angle (270), like birky_cat.py's
# d-air. The tip's top edge (dy-r=64) is below the hurtbox bottom (dy 59). PM3.6 Marth
# `AttackAirLw`, ⚠ playtest / rukaidata-confirm. NOTE: Marth's real d-air stall-then-fall
# is a MOVEMENT mechanic (kin to fast-fall #261), not move data — deferred; this is the
# spike hitbox only. Completes the #294 sword aerials.
_NARZ_DAIR = MoveData(
    name="dair",
    in_air=True,
    startup=6,
    active=3,
    recovery=16,  # 6 + 3 + 16 = 25
    hitboxes=(
        # TIP (box 0): farthest-below + strongest (the spike).
        Hitbox(circle=Circle(dx=24, dy=76, r=12), damage=12.0, angle=270,
               base_knockback=15.0, knockback_growth=80.0),
        # BASE (box 1): nearer + weaker.
        Hitbox(circle=Circle(dx=24, dy=56, r=14), damage=9.0, angle=270,
               base_knockback=10.0, knockback_growth=60.0),
    ),
)

# --- Smashes (slice 5 of #327 / #294): the archetype's signature KO tools ----------
# Narz's smashes are the strongest disjoint tippers — 2-box (tip box FIRST, priority =
# tuple order, so the far tip wins on overlap), chargeable via the mechanic in #371/#377.
# PM3.6 Marth (AttackS4 / AttackHi4 / AttackLw4), ⚠ playtest / rukaidata-confirm-later —
# the same fidelity caveat every Narz move carries (#290).

# Forward-smash: Marth's iconic spacing KO. Far tip = the KO hit; near base = a punished
# whiff. The strongest, longest tipper in the kit.
_NARZ_FSMASH = MoveData(
    name="fsmash",
    in_air=False,
    chargeable=True,
    startup=10,
    active=3,
    recovery=31,  # 10 + 3 + 31 = 44 (PM3.6 total / IASA ballpark)
    hitboxes=(
        # TIP (box 0): farthest + strongest — the signature KO.
        Hitbox(circle=Circle(dx=78, dy=30, r=12), damage=18.0, angle=361,
               base_knockback=35.0, knockback_growth=95.0),
        # BASE (box 1): near the body + weaker.
        Hitbox(circle=Circle(dx=52, dy=30, r=14), damage=14.0, angle=361,
               base_knockback=25.0, knockback_growth=72.0),
    ),
)

# Up-smash: a tall vertical sword arc above the head — the tip (higher) is the anti-air KO
# sweetspot. angle 90 (up).
_NARZ_USMASH = MoveData(
    name="usmash",
    in_air=False,
    chargeable=True,
    startup=9,
    active=3,
    recovery=28,  # 9 + 3 + 28 = 40
    hitboxes=(
        # TIP (box 0): highest above the head + strongest.
        Hitbox(circle=Circle(dx=22, dy=-16, r=12), damage=18.0, angle=90,
               base_knockback=32.0, knockback_growth=95.0),
        # BASE (box 1): head level + weaker.
        Hitbox(circle=Circle(dx=22, dy=6, r=14), damage=13.0, angle=90,
               base_knockback=22.0, knockback_growth=72.0),
    ),
)

# Down-smash: hits FRONT then BEHIND, low along the ground — two temporal windows (#204),
# each a 2-box tipper (tip FIRST). Front [6,7] ahead, back [13,14] behind (dx < 0).
_NARZ_DSMASH = MoveData(
    name="dsmash",
    in_air=False,
    chargeable=True,
    startup=5,
    active=9,      # spans the front [6,7] + back [13,14] windows
    recovery=20,   # 5 + 9 + 20 = 34
    hitboxes=(
        # FRONT TIP (box 0): far ahead, low + strong.
        Hitbox(circle=Circle(dx=52, dy=48, r=12), damage=15.0, angle=361,
               base_knockback=30.0, knockback_growth=80.0, active_start=6, active_end=7),
        # FRONT BASE (box 1): nearer + weaker.
        Hitbox(circle=Circle(dx=34, dy=48, r=14), damage=12.0, angle=361,
               base_knockback=22.0, knockback_growth=65.0, active_start=6, active_end=7),
        # BACK TIP (box 2): far behind, low + strong.
        Hitbox(circle=Circle(dx=-52, dy=48, r=12), damage=13.0, angle=361,
               base_knockback=28.0, knockback_growth=78.0, active_start=13, active_end=14),
        # BACK BASE (box 3): nearer-behind + weaker.
        Hitbox(circle=Circle(dx=-34, dy=48, r=14), damage=10.0, angle=361,
               base_knockback=20.0, knockback_growth=63.0, active_start=13, active_end=14),
    ),
)

NARZ_FIGHTER_DATA = FighterData(
    # Slice 2 (#299): Narz's own forward-tilt (the disjoint+tipper identity move) under
    # the "ftilt" key (forward+A via the move-select seam, combat/move_select.py); the
    # default "attack" placeholder is kept as the neutral-A fallback. Other slots reuse
    # the default cat until their slices land (#294). Body still the default (#290 v1).
    hurtbox=_DEFAULT.hurtbox,
    moves={**_DEFAULT.moves, "ftilt": _NARZ_FTILT, "jab": _NARZ_JAB,
           "dtilt": _NARZ_DTILT, "utilt": _NARZ_UTILT, "nair": _NARZ_NAIR,
           "fair": _NARZ_FAIR, "bair": _NARZ_BAIR, "uair": _NARZ_UAIR,
           "dair": _NARZ_DAIR, "fsmash": _NARZ_FSMASH, "usmash": _NARZ_USMASH,
           "dsmash": _NARZ_DSMASH},
    crouch_size=_DEFAULT.crouch_size,
    crouch_hurtbox=_DEFAULT.crouch_hurtbox,
    prone_size=_DEFAULT.prone_size,
    prone_hurtbox=_DEFAULT.prone_hurtbox,
    # the light-medium swordfighter scalars (#290) — only the deltas from baseline;
    # max_jumps/move_speed/max_fall_speed match Mario, so they stay defaulted.
    weight=87,
    gravity=0.45,
    jump_vel=-12,
)
