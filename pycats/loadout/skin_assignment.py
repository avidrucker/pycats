"""Skin-assignment layer — per-Character availability + same-Character distinctness.

Ratified on #748 (Option A: one domain layer; representation (ii) ``Character.extra_skin_keys``).
Answers the two questions #676 (live char-select) and #718 (sim) both need, so neither
adapter re-implements them:

- ``available_skins(character)`` — which Skins this Character may wear: the shared OG pool
  (``SHARED_SKIN_KEYS``) plus the Character's own ``extra_skin_keys``. Never another
  Character's theme.
- ``assign_distinct_skins(selections)`` — two players who picked the **same** Character get
  distinct Skins (the second falls to the next available Skin in that Character's pool).

Pure: imports no pygame / sim / UI.
"""

from __future__ import annotations

from collections.abc import Sequence

from .character import Character
from .registry import SKINS
from .selection import Selection
from .skin import Skin

# The shared cosmetic pool every Character may wear — the original six OG skins.
# Character-owned themes (the #677 base themes, future character-specific skins) live on
# each Character's ``extra_skin_keys``, NOT here. Order = char-select grid / cycle order.
SHARED_SKIN_KEYS: tuple[str, ...] = ("ghost", "calico", "tabby", "void", "tiger", "bengal")


def available_skins(character: Character) -> list[Skin]:
    """The Skins ``character`` may wear: the shared OG pool + the Character's own extras.

    Order is shared keys first (grid order) then the Character's extras; deduped, with any
    key absent from the registry skipped. A Character never receives another Character's theme.
    """
    out: list[Skin] = []
    seen: set[str] = set()
    for key in (*SHARED_SKIN_KEYS, *character.extra_skin_keys):
        if key in seen:
            continue
        seen.add(key)
        skin = SKINS.get(key)
        if skin is not None:
            out.append(skin)
    return out


def assign_distinct_skins(selections: Sequence[Selection]) -> list[Selection]:
    """De-collide Skins among players who picked the **same** Character.

    Returns a new list positionally matching ``selections``. The first player on a given
    Character keeps their Skin; a later player on that same Character whose Skin is already
    taken is moved to the next available Skin in the Character's pool (``available_skins``).
    Players on different Characters are never affected. If a Character's pool is exhausted,
    the collision is left as-is (best effort — nothing better to give).
    """
    result: list[Selection] = []
    used_by_character: dict[str, set[str]] = {}
    for selection in selections:
        character = selection.character
        used = used_by_character.setdefault(character.key, set())
        skin = selection.skin
        if skin.key in used:
            for candidate in available_skins(character):
                if candidate.key not in used:
                    skin = candidate
                    break
        used.add(skin.key)
        result.append(selection if skin is selection.skin else Selection(character, skin))
    return result
