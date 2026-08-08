"""
Purpose: Central configuration package.

Contents (split from the former flat config.py, #934 / epic #833):
- screen  — SCREEN_WIDTH, SCREEN_HEIGHT, FPS, tick_fps
- physics — combat/physics tuning (gravity, movement, dodges, ledges, shield,
            knockback/hitstun/hitlag, PX_PER_UNIT)
- stage   — platforms, Starting Point (FD), blast zones, stocks, respawn
- render  — fighter size/position/colors, cat features, tail, shield colour, HUD
- menu    — win/char-select/main-menu chrome, menu cooldowns, font sizes/scales

The import surface is unchanged: `from pycats.config import <NAME>` still resolves
every constant (the submodules are re-exported below), so no call site changed.

Use: Shared constants across modules for tuning gameplay and UI.
"""

# Cat character definitions.
# Archived to pycats/characters/og_skins.py (#131, Part 1 of epic #127): these six
# entries are colour-skins of one cat, not characters. CAT_CHARACTERS re-exports the
# archive so existing consumers (char_select, game, sim/runner) read the one source.
from ..characters.og_skins import (
    OG_SKINS as CAT_CHARACTERS,  # noqa: F401 (re-export; consumed by sim/runner, char_select)
)
from .menu import *  # noqa: F403
from .physics import *  # noqa: F403
from .render import *  # noqa: F403
from .screen import *  # noqa: F403
from .stage import *  # noqa: F403
