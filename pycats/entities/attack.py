"""
Purpose: Defines the Attack hit-box sprite.

Contents:
- Attack is a pygame.sprite.Sprite
- Spawned when a player attacks
- Lives for a fixed number of frames, then self-deletes
- Positioned based on the owner player's facing direction

Use: Used to detect hit interactions between players.
"""

import pygame
from ..config import ATTACK_LIFETIME, ATTACK_SIZE

class Attack(pygame.sprite.Sprite):
    """Simple rectangular hit-box that disappears after N frames."""
    COLOR = (255, 60, 60, 180)   # semi-transparent red

    def __init__(self, owner):
        super().__init__()
        self.frames_left = ATTACK_LIFETIME

        offset_x = owner.rect.width // 2 + 4
        x = owner.rect.centerx + (offset_x if owner.facing_right else -offset_x)
        y = owner.rect.centery - ATTACK_SIZE[1] // 2

        self.image = pygame.Surface(ATTACK_SIZE, pygame.SRCALPHA)
        self.image.fill(self.COLOR)
        self.rect = self.image.get_rect(center=(x, y))

    # called every frame by sprite.Group.update()
    def update(self):
        self.frames_left -= 1
        if self.frames_left <= 0:
            self.kill()
