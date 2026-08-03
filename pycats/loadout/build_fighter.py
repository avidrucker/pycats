"""The application port both the sim and the live game call (#672 domain, spec §2).

``build_fighter(Selection) -> BuiltFighter`` composes the two resolvers into the
one seam that replaces today's two parallel constructors (``sim.runner`` colouring
from ``CAT_CHARACTERS`` vs the live game from ``palette_for``). It always returns a
Skin — headless sim runs simply ignore it. There is **no ``if`` on the key**: the
placeholder flows through here like any other Selection.

Pure: imports no pygame / sim / UI.
"""

from __future__ import annotations

from .resolvers import fighter_data_of, palette_of
from .selection import BuiltFighter, Selection


def build_fighter(selection: Selection) -> BuiltFighter:
    return BuiltFighter(
        fighter_data=fighter_data_of(selection.character),
        skin=palette_of(selection.skin),
    )
