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
from pycats.combat.data import FighterData

NARZ_FIGHTER_DATA = FighterData(
    # Placeholders this slice (reuse the default cat) — Narz's real disjoint/tipper
    # moves + body are later slices under #294.
    hurtbox=_DEFAULT.hurtbox,
    moves=_DEFAULT.moves,
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
