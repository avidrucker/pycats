"""
Purpose: Defines the Platform class.

Contents:
- Subclass of pygame.sprite.Sprite
- Handles thin and thick platform logic
- Visual differentiation based on thickness

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
        color = (164, 113, 73) if not thin else (193, 153, 112)
        self.image = pygame.Surface(rect.size)
        self.image.fill(color)
        self.rect = rect
