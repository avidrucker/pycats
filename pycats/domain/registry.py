"""Selectable registries + the unknown-key → placeholder resolver (#672 domain, spec §4).

``CHARACTERS`` / ``SKINS`` are the *selectable* rosters; the placeholder is
deliberately **absent from both**, so char-select can never land on it.
``resolve_selection()`` maps a (possibly unknown / mis-keyed) pair to a Selection,
routing anything unrecognised to the placeholder in **both** halves — the single
fallthrough that replaces the old ``if key == "testcat"`` (in ``load_fighter_data``
and ``palette_for``) plus the ``_NEUTRAL`` unknown-key branch.

Roster identity data (which archetypes exist + their display names / default skins)
is imported from ``characters.roster`` as the single source of truth for now; a
later phase may invert the dependency so ``roster`` reads from the domain instead.
Pure: imports no pygame / sim / UI.
"""

from __future__ import annotations

from ..characters.palettes import load_palettes
from ..characters.roster import (
    ARCHETYPE_DEFAULT_SKIN,
    ARCHETYPE_EXTRA_SKINS,
    ARCHETYPE_NAME,
    ARCHETYPE_ROSTER,
)
from .character import Character
from .placeholder import PLACEHOLDER_CHARACTER, PLACEHOLDER_SKIN
from .selection import Selection
from .skin import Skin

SKINS: dict[str, Skin] = {key: Skin.from_palette_dict(key, d) for key, d in load_palettes().items()}

CHARACTERS: dict[str, Character] = {
    key: Character(
        key=key,
        name=ARCHETYPE_NAME[key],
        default_skin_key=ARCHETYPE_DEFAULT_SKIN[key],
        extra_skin_keys=ARCHETYPE_EXTRA_SKINS[key],
    )
    for key in ARCHETYPE_ROSTER
}


def character_for(char_key) -> Character:
    """The Character for a key, or the placeholder for an unknown / None key.

    Reproduces ``combat.data.load_fighter_data``'s mechanics resolution (a known
    archetype → that cat; anything else → the default, via the placeholder's
    ``"testcat"`` key), so an adapter can build a Selection with an *explicit* skin
    without re-implementing that fallback. Used by the sim / live constructors in
    Phase 1b, where cosmetics are still resolved separately (#672).
    """
    return CHARACTERS.get(char_key, PLACEHOLDER_CHARACTER)


def resolve_selection(char_key, skin_key=None) -> Selection:
    """Resolve a (character-key, optional skin-key) pair to a Selection.

    Unknown character keys → the placeholder character; an unknown / omitted skin
    key falls to the character's default skin, and an unrecognised skin → the
    placeholder skin. So a typo renders *visibly* as the gray placeholder in both
    halves, never silently as a real cat.
    """
    character = CHARACTERS.get(char_key, PLACEHOLDER_CHARACTER)
    skin_key = skin_key or character.default_skin_key
    skin = SKINS.get(skin_key, PLACEHOLDER_SKIN)
    return Selection(character, skin)
