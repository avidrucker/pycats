"""Selection and BuiltFighter (#672 domain, spec §2).

- ``Selection = (Character, Skin)`` — what a player commits.
- ``BuiltFighter = (FighterData, Skin)`` — what the ``build_fighter`` port returns.

Pure: imports no pygame / sim / UI.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

from .character import Character
from .skin import Skin

if TYPE_CHECKING:  # avoid a runtime import of combat.data just for the annotation
    from ..combat.data import FighterData


class Selection(NamedTuple):
    character: Character
    skin: Skin


class BuiltFighter(NamedTuple):
    fighter_data: FighterData
    skin: Skin
