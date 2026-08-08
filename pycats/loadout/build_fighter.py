"""The application port both the sim and the live game call (#672 domain, spec §2).

``build_fighter(Selection) -> BuiltFighter`` composes the two resolvers into the
one seam that replaces today's two parallel constructors (``sim.runner`` colouring
from ``CAT_CHARACTERS`` vs the live game from ``palette_for``). It always returns a
Skin — headless sim runs simply ignore it. There is **no ``if`` on the key**: the
placeholder flows through here like any other Selection.

Pure: imports no pygame / sim / UI.
"""

from __future__ import annotations

from .modifiers import apply
from .resolvers import fighter_data_of, palette_of
from .selection import BuiltFighter, Selection


def build_fighter(selection: Selection) -> BuiltFighter:
    # Apply any drafted ROUNDS cards at this seam (ADR-0014 §1: once, before
    # Fighter.__init__ caches the fields). With the default empty card list,
    # `apply` returns the baseline unchanged → byte-identical to today.
    return BuiltFighter(
        fighter_data=apply(fighter_data_of(selection.character), selection.cards),
        skin=palette_of(selection.skin),
    )
