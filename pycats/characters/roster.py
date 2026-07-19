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

# Default cosmetic palette per archetype (an OG skin; cosmetic only, ⚠ playtest-TBD).
# Default OG-skin KEY per archetype — the single source (#650): the skin a character
# wears until a player cycles it on the char-select screen (Part 3 of #127).
ARCHETYPE_DEFAULT_SKIN = {
    "nalio": "red-blue",  # base theme (#677): red body, blue accents
    "birky": "pink-red",  # base theme (#677): pink body, red accents
    "narz": "blue-black",  # base theme (#677): blue body, black accents
}

# Default cosmetic palette per archetype (derived from ARCHETYPE_DEFAULT_SKIN, cosmetic-only).
ARCHETYPE_PALETTE = {archetype: _PAL[skin] for archetype, skin in ARCHETYPE_DEFAULT_SKIN.items()}

# Display name shown on the char-select tile (the archetype, not the palette).
ARCHETYPE_NAME = {
    "nalio": "Nalio",
    "birky": "Birky",
    "narz": "Narz",
}

# Neutral fallback cosmetic for any key with no archetype/OG palette.
_NEUTRAL = {"name": "?", "color": (200, 200, 200), "stripe_color": (150, 150, 150), "eye_color": (0, 0, 0)}

# The `testcat` fixture (#591) is a test scaffold, not a playable cat — it must read on
# screen as clearly non-standard. Per DP1 (#672 ruling, 2026-07-06) it renders as **flat
# uniform gray** — body / stripe / eye all (128, 128, 128) — matching `domain.placeholder`
# PLACEHOLDER_SKIN. Uniform gray makes the features vanish by colour, so legibility is
# carried by **black feature outlines** drawn in render_battle (#694), not by colour
# contrast — the same #546 outline-legibility basis. Opaque, not alpha. Supersedes the
# #636 three-tone gray. This dict is the shipped cosmetic source until Phase 2/3 wire the
# domain into the live adapter.
_TESTCAT = {"name": "Test", "color": (128, 128, 128), "stripe_color": (128, 128, 128), "eye_color": (128, 128, 128)}


def palette_for(key):
    """Resolve a selection key to a cosmetic palette: the `testcat` placeholder (#636) →
    the archetype's default → the OG skin of that name (legacy / sim-runner-parity keys) →
    a neutral fallback. Never raises. The *fighter data* for a key is resolved separately
    via `load_fighter_data` (which likewise defaults the cat for unknown keys)."""
    if key == "testcat":
        return _TESTCAT
    return ARCHETYPE_PALETTE.get(key) or _PAL.get(key) or _NEUTRAL
