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
    from .cards import Card


class Selection(NamedTuple):
    character: Character
    skin: Skin
    # Drafted ROUNDS cards (DEV 2, #1196). Defaults to no cards, so every existing
    # Selection is unchanged and `build_fighter` applies the empty patch → the
    # fighter data is byte-identical to today (ADR-0014 inert wiring). Nothing
    # produces a non-empty list until the draft (DEV 6+).
    cards: tuple[Card, ...] = ()


class BuiltFighter(NamedTuple):
    fighter_data: FighterData
    skin: Skin
