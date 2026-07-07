"""The Player seat, decomposed into three independent seams (#672 domain, spec §3).

Today ``Player.char_name`` is one string doing four jobs. The refactor splits the
seat's *identity* into three seams that vary independently:

- ``PlayerNumberSlot`` — 1 / 2 (v1); the stable identity + win-attribution key.
- ``PlayerTeamColor`` — RED / BLUE accent (v1); GREEN / YELLOW later.
- ``PlayerName``      — "P1" / "P2" label (v1); absorbs today's nickname (#478),
  custom names post-v1.

Number is primary; team_color and name *default from* it (composition, not braid)
but stay independently overridable. **Every seam keeps its ``Player…`` prefix** so
a bare ``Name`` / ``Color`` / ``Slot`` can't shadow a builtin, a pygame symbol, or
an existing domain term. Pure: imports no pygame / sim / UI.
"""

from __future__ import annotations

from enum import Enum
from typing import NamedTuple


class PlayerNumberSlot(int):
    """The seat number (1 or 2 in v1). Behaves as an int; the stable identity."""


class PlayerTeamColor(Enum):
    RED = "red"  # → P1_UI_COLOR accent
    BLUE = "blue"  # → P2_UI_COLOR accent
    # v-next: GREEN, YELLOW


class PlayerName(str):
    """The display label ("P1"/"P2" by default). Absorbs today's nickname (#478)."""


class PlayerIdentity(NamedTuple):
    number: PlayerNumberSlot
    team_color: PlayerTeamColor
    name: PlayerName

    @classmethod
    def for_slot(cls, n: int) -> PlayerIdentity:
        """The v1 defaults: team_color and name derive from the seat number."""
        return cls(
            PlayerNumberSlot(n),
            PlayerTeamColor.RED if n == 1 else PlayerTeamColor.BLUE,
            PlayerName(f"P{n}"),
        )
