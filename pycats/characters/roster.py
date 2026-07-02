"""Selectable archetype roster + default cosmetic palettes (selectability, #268).

Completes #127 Part 1: the char-select roster is the real PM-archetype fighters (the
keys `load_fighter_data` knows), NOT the six OG colour-skins. Each archetype carries a
DEFAULT palette (one of the OG skins) for its cosmetic colours until the #127 Part-3
skin-cycle lets players change it. The roster grows as #117 archetypes are implemented.

Presentation-only data (palettes from `palettes.load_palettes()`); no sim/golden
dependency.
"""
from .palettes import load_palettes

_PAL = load_palettes()

# Implemented archetypes only (Nalio #142, Birky #228, Narz #294). Tuple order = grid order.
ARCHETYPE_ROSTER = ("nalio", "birky", "narz")

# Default cosmetic palette per archetype (an OG skin; cosmetic only, playtest-TBD).
ARCHETYPE_PALETTE = {
    "nalio": _PAL["calico"],  # balanced all-rounder → warm orange
    "birky": _PAL["ghost"],   # floaty featherweight → light/round
    "narz": _PAL["void"],     # disjointed swordfighter → sleek/dark
}

# Display name shown on the char-select tile (the archetype, not the palette).
ARCHETYPE_NAME = {
    "nalio": "Nalio",
    "birky": "Birky",
    "narz": "Narz",
}

# Neutral fallback cosmetic for any key with no archetype/OG palette.
_NEUTRAL = {"name": "?", "color": (200, 200, 200),
            "stripe_color": (150, 150, 150), "eye_color": (0, 0, 0)}


def palette_for(key):
    """Resolve a selection key to a cosmetic palette: the archetype's default →
    the OG skin of that name (legacy / sim-runner-parity keys) → a neutral fallback.
    Never raises. The *fighter data* for a key is resolved separately via
    `load_fighter_data` (which likewise defaults the cat for unknown keys)."""
    return ARCHETYPE_PALETTE.get(key) or _PAL.get(key) or _NEUTRAL
