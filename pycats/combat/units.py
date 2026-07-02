"""pycats/combat/units.py

Purpose: the single authoring-time seam from Smash *units* to pixels (#195).

pycats enters combat scalars (damage, %, angle, BKB, KBG, weight, frames) RAW, and
scales SPATIAL values (hitbox radii + offsets) by `config.PX_PER_UNIT ≈ 5.4 px/unit`
(the #120 finding). `u(units)` is that conversion, named once so new character/move
spatial data is authored through it instead of copying a bare `× 5.4` by hand.

The SIM stays integer-pixel (a determinism asset, #80): `u` rounds to an int, so
`u(3.5) == 19` exactly. Existing baked literals are kept byte-identical (ADR-0003 C1)
and their derivation comments now cite `PX_PER_UNIT` by name rather than the magic 5.4.
"""
from __future__ import annotations

from ..config import PX_PER_UNIT


def u(units: float) -> int:
    """Convert Smash spatial *units* to integer pixels via PX_PER_UNIT.

    `round(units * PX_PER_UNIT)` — the sim is integer-pixel (#80), so the result is
    an int. E.g. `u(3.5) == 19`, `u(3.1) == 17`. Use for hitbox radii/offsets when
    authoring character data; combat scalars stay raw.
    """
    return round(units * PX_PER_UNIT)
