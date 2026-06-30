"""FighterData for "Birky" — the Kirby archetype (floaty featherweight). Slice 1 of #228.

Birky is the **first** fighter to diverge on the per-fighter MOVEMENT SCALARS. Values
from the #229 scoping spike (PM Kirby, proportional-to-Mario; pin/playtest later):

    weight 70 · gravity 0.42 · max_fall_speed 12 · move_speed 5 · max_jumps 6 · jump_vel -11

Per #120, these scalars are entered RAW (the ×5.4 unit scale is for *spatial* values,
not needed this slice).

Placeholders reused from the default cat (slice 1 = scalars only):
  - `hurtbox`, `moves`, crouch/prone geometry — Birky's real moves are **slice 2**;
  - per-fighter body size is **not** a `FighterData` field (the rendered `stand_size`
    is the global `config.PLAYER_SIZE`), so a smaller round body is out of scope here.

Caveat (#229): pycats has a single `move_speed` knob (ground == air), so Kirby's
slow-walk / fast-air split can't be captured — `move_speed` leans to the
slow-featherweight identity. The genuine `fast-fall` mechanic is a separate, shared
engine ticket; selectability (making Birky human-pickable) is gated on #117/#127.
"""
from pycats.characters.default_cat import DEFAULT_FIGHTER_DATA as _DEFAULT
from pycats.combat.data import FighterData

BIRKY_FIGHTER_DATA = FighterData(
    # placeholders reused from the default cat (this slice diverges on scalars only)
    hurtbox=_DEFAULT.hurtbox,
    moves=_DEFAULT.moves,
    crouch_size=_DEFAULT.crouch_size,
    crouch_hurtbox=_DEFAULT.crouch_hurtbox,
    prone_size=_DEFAULT.prone_size,
    prone_hurtbox=_DEFAULT.prone_hurtbox,
    # the featherweight movement scalars (#229)
    weight=70,
    gravity=0.42,
    max_fall_speed=12,
    move_speed=5,
    max_jumps=6,
    jump_vel=-11,
)
