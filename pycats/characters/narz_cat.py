"""FighterData for "Narz" — the Marth archetype (disjointed swordfighter). Slice 1 of #294.

Narz's *mobility* is near-Mario (#290 finding): only the **weight** and a slightly
**floatier gravity** (plus a touch lower jump velocity) differ from the default/Mario
baseline. The archetype identity is NOT in these scalars — it is in **move geometry**
(disjoint reach + tipper), which slice 2 (the forward-tilt) introduces.

Values from the #290 scoping spec (PM3.6 Marth; ⚠ playtest / rukaidata-confirm later):

    weight 87 · gravity 0.45 · jump_vel -12   (deltas)
    max_jumps 2 · move_speed 6 · max_fall_speed 13   (= baseline, left as defaults)

Per #120, these scalars are entered RAW (the ×5.4 unit scale is for *spatial* values).

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

NARZ_FIGHTER_DATA = FighterData(
    # Slice 2 (#299): Narz's own forward-tilt (the disjoint+tipper identity move) under
    # the "ftilt" key (forward+A via the move-select seam, combat/move_select.py); the
    # default "attack" placeholder is kept as the neutral-A fallback. Other slots reuse
    # the default cat until their slices land (#294). Body still the default (#290 v1).
    hurtbox=_DEFAULT.hurtbox,
    moves={**_DEFAULT.moves, "ftilt": _NARZ_FTILT},
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
