"""The two independent resolvers (#672 domain, spec §2).

- ``fighter_data_of(Character) -> FighterData`` — mechanics, wrapping the existing
  ``combat.data.load_fighter_data`` with the key now made explicit.
- ``palette_of(Skin) -> Skin`` — cosmetics, a near-identity (the Skin already *is*
  the cosmetic value).

They are kept separate on purpose: skin-cycling (#650) changes cosmetics with zero
change to fighter data, so fusing them would re-braid the two concerns this epic
exists to separate. ``combat.data`` imports no pygame at module load (its per-cat
data is lazy-imported), so importing this module stays pygame-free.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..combat.data import load_fighter_data

if TYPE_CHECKING:
    from ..combat.data import FighterData
    from .character import Character
    from .skin import Skin


def fighter_data_of(character: Character) -> FighterData:
    return load_fighter_data(character.key)


def palette_of(skin: Skin) -> Skin:
    return skin
