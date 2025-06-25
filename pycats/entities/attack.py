"""
Purpose: Defines the Attack hit-box sprite.

Contents:
- Attack is a pygame.sprite.Sprite
- Spawned when a player attacks
- Lives for a fixed number of frames, then self-deletes
- Positioned based on the owner player's facing direction

Use: Used to detect hit interactions between players.
"""

#### TODO: implement grabbing, which puts attacker into grabbing and, if successful, puts the defender into grabbed state, the duration is dependent on defender damage percent (low damager percent == shorter grab durations)
#### TODO: implement parameterized attack colors, to distinguish whom is attacking
#### TODO: implement attack hit-boxes that are larger for heavy characters and smaller for light characters
#### TODO: implement ranged attacks such as fireballs & lazer blasts
#### TODO: implement throw attacks that can throw the opponent off the stage, with a directional key (forward, backward, up, down), and throw attacks can only be executed while the attacker is in grabbing state and the opponent is in grabbed state
#### TODO: implement grab attacks ("pummeling") that can deal minor damage to a grabbed opponent
#### TODO: implement grab escape mechanics where the grabbed player can mash their inputs to escape sooner
#### TODO: implement ability for some attacks to hit more than one opponent

import pygame
from ..config import ATTACK_LIFETIME, ATTACK_SIZE, HIT_DAMAGE, KNOCKBACK_BASE, KNOCKBACK_SCALE

class Attack(pygame.sprite.Sprite):
    """Simple rectangular hit-box that disappears after N frames, and that can either vanish on hit or persist visually."""
    COLOR = (255, 60, 60, 180)   # semi-transparent red

    def __init__(self, owner, damage: int = HIT_DAMAGE, disappear_on_hit=False, base_kb=KNOCKBACK_BASE, kb_scale=KNOCKBACK_SCALE, angle=0):
        super().__init__()
        self.owner  = owner
        self.damage = damage
        self.disappear_on_hit = disappear_on_hit
        self.active = True

        self.frames_left = ATTACK_LIFETIME

        offset_x = owner.rect.width // 2 + 4
        x = owner.rect.centerx + (offset_x if owner.facing_right else -offset_x)
        y = owner.rect.centery - ATTACK_SIZE[1] // 2

        self.image = pygame.Surface(ATTACK_SIZE, pygame.SRCALPHA)
        self.image.fill(self.COLOR)
        self.rect = self.image.get_rect(center=(x, y))

        self.base_kb  = base_kb
        self.kb_scale = kb_scale
        self.angle    = angle

    # called every frame by sprite.Group.update()
    def update(self):
        self.frames_left -= 1
        if self.frames_left <= 0:
            self.kill()
