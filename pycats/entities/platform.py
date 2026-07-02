"""
Purpose: Defines the Platform class.

Contents:
- Subclass of pygame.sprite.Sprite (for Group membership; holds rect + thin only)
- Handles thin and thick platform logic
- Visual differentiation (thickness colour) is applied by render_battle (#317)

Use: Used to build the stage (collision platforms).
"""

import pygame  # type: ignore


class Platform(pygame.sprite.Sprite):
    """Axis-aligned rectangular platform.

    *thin*  - allows pass-through from below, drop-through via DOWN while grounded.
    *thick* - solid on all sides (e.g. main stage).
    """

    def __init__(self, rect: pygame.Rect, thin: bool = False):
        super().__init__()
        self.thin = thin
        self.rect = rect
        # #317/H-b: no owned render Surface — render_battle paints the thickness
        # colour from `thin`/`rect`. The Sprite base stays (callers add Platforms
        # to pygame.sprite.Groups); physics reads only `rect`/`thin`.
