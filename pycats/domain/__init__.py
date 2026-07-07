"""pycats.domain — the pure DDD core of the skin / character / selection model (#672).

Imports no pygame / sim / UI (enforced by ``tests/test_domain_model.py``'s import-
purity check). This package is introduced *unwired* in Phase 1a; the sim + live
adapters are rewired through ``build_fighter`` in Phase 1b. See the design spec:
``docs/research-spec-675-skin-char-model.md``.
"""

from __future__ import annotations

from .build_fighter import build_fighter
from .character import Character
from .placeholder import PLACEHOLDER_CHARACTER, PLACEHOLDER_SKIN
from .player_identity import PlayerIdentity, PlayerName, PlayerNumberSlot, PlayerTeamColor
from .registry import CHARACTERS, SKINS, resolve_selection
from .resolvers import fighter_data_of, palette_of
from .selection import BuiltFighter, Selection
from .skin import RGB, Skin

__all__ = [
    "RGB",
    "Skin",
    "Character",
    "Selection",
    "BuiltFighter",
    "PlayerNumberSlot",
    "PlayerTeamColor",
    "PlayerName",
    "PlayerIdentity",
    "PLACEHOLDER_CHARACTER",
    "PLACEHOLDER_SKIN",
    "CHARACTERS",
    "SKINS",
    "resolve_selection",
    "fighter_data_of",
    "palette_of",
    "build_fighter",
]
