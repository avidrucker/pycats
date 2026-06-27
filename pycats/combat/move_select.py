"""pycats/combat/move_select.py

Move-selection seam (#143, Phase 2 epic #142): map an input context
``(direction × ground/air × A-vs-B)`` to a character's move key, with fallback
to whatever the character actually defines. Pure (no pygame); the entity layer
(`fighter_input`) computes the direction token and looks up the resolved key.

Move-key naming convention (the keys a character's `FighterData.moves` may use;
per-move authoring slices drop a `MoveData` under the matching key):
  ground normals : jab, ftilt, utilt, dtilt   (+ dash later)
  aerials        : nair, fair, bair, uair, dair
  specials (B)   : neutral_b, side_b, up_b, down_b
``"attack"`` is the legacy **neutral-ground alias** kept as the generic A
fallback (Nalio's d-tilt + the default cat's jab both live under it today), so a
character with a partial kit behaves exactly as before this seam.

Direction tokens (computed by the caller from raw input + facing):
  "neutral", "up", "down", "forward" (toward facing), "back" (away from facing).
On the ground "forward"/"back" both resolve to the f-tilt (Smash has no b-tilt).
"""
from __future__ import annotations

# Canonical key per (direction, on_ground, is_special). Forward/back collapse to
# ftilt on the ground; in the air they split fair/bair.
_GROUND_A = {"neutral": "jab", "up": "utilt", "down": "dtilt",
             "forward": "ftilt", "back": "ftilt"}
_AIR_A = {"neutral": "nair", "up": "uair", "down": "dair",
          "forward": "fair", "back": "bair"}
_SPECIAL = {"neutral": "neutral_b", "up": "up_b", "down": "down_b",
            "forward": "side_b", "back": "side_b"}


def select_move_key(direction: str, on_ground: bool, is_special: bool) -> str:
    """Canonical move key for an input context (no fallback). `direction` is one
    of neutral/up/down/forward/back."""
    if is_special:
        return _SPECIAL[direction]
    return (_GROUND_A if on_ground else _AIR_A)[direction]


def resolve_move_key(available, direction: str, on_ground: bool,
                     is_special: bool):
    """The move key to actually play, or None if nothing applies.

    Prefers the canonical key; if the character doesn't define it, falls back:
      - special (B): no fallback — None (no-op) when the special is undefined;
      - ground A: the ``"attack"`` neutral alias, if present;
      - air A: ``"nair"`` if present, else the ``"attack"`` alias.
    ``available`` is any container of the character's move keys (dict or set).
    """
    primary = select_move_key(direction, on_ground, is_special)
    if primary in available:
        return primary
    if is_special:
        return None
    if not on_ground and "nair" in available:
        return "nair"
    return "attack" if "attack" in available else None
