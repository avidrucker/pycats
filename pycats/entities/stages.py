"""Named stage layouts (#660).

A stage is a **named, reusable platform set** — the seed the post-v1 stage-selection
epic builds on, replacing the old pile of inline ``Platform()`` calls in ``game.py``.

v1 ships exactly one *player-facing* stage: **"Starting Point"**, pycats' flat Final
Destination, sized to the PM FD measurements researched in #659
(``docs/research/2026-07-06-pm-final-destination-measurements.md``). Human players get
only this stage for now (``DEFAULT_PLAYER_STAGE``).

The Battlefield-like arena the demos/sims still run on is defined by ``config``'s
``THICK_``/``THIN_PLAT`` dicts and built by ``sim.runner.build_stage`` — unchanged by
this ticket. It is mirrored here as a named layout (``BATTLEFIELD``, single-sourced from
the same config dicts, so it can't drift) purely so the future stage-select epic has a
second registry entry; it is **not** a player stage yet.
"""

from dataclasses import dataclass

import pygame

from ..config import (
    STARTING_POINT_DICT,
    THICK_PLAT_DICT,
    THIN_PLAT_DICT_L,
    THIN_PLAT_DICT_R,
)
from .platform import Platform


@dataclass(frozen=True)
class StageLayout:
    """A named platform set. ``plats`` is a tuple of ``(dict, thin)`` specs, where
    ``dict`` carries ``x/y/w/h`` (config's platform dicts) and ``thin`` marks a
    pass-through platform (non-grabbable; see ``ledges_from_platforms``)."""

    name: str
    plats: tuple

    def build(self) -> list:
        """Fresh ``Platform`` sprites for this layout (callers own the list, exactly
        like the old inline ``game.py`` build)."""
        return [Platform(pygame.Rect(d["x"], d["y"], d["w"], d["h"]), thin=thin) for d, thin in self.plats]


# pycats' flat Final Destination — one solid main platform, no side platforms (#659/#660).
STARTING_POINT = StageLayout("Starting Point", ((STARTING_POINT_DICT, False),))

# The legacy demo/sim arena, named for the future stage-select epic. Single-sourced from
# the same config dicts the sims build from, so the two definitions can't diverge.
BATTLEFIELD = StageLayout(
    "Battlefield",
    (
        (THICK_PLAT_DICT, False),
        (THIN_PLAT_DICT_L, True),
        (THIN_PLAT_DICT_R, True),
    ),
)

STAGES = {s.name: s for s in (STARTING_POINT, BATTLEFIELD)}

# What human players get for v1 (stage selection is post-v1).
DEFAULT_PLAYER_STAGE = STARTING_POINT
