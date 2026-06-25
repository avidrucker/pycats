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

import pygame  # type: ignore
from ..config import ATTACK_SIZE  # render-only: sizes the drawn hit-box rect
from ..combat.geometry import resolve_circle


class Attack(pygame.sprite.Sprite):
    """Simple rectangular hit-box that disappears after N frames, and that can either vanish on hit or persist visually.

    Task 5: Attack now carries an absolute hitbox circle (hit_cx, hit_cy, hit_r)
    resolved from the move's Hitbox.circle at spawn time using the owner's
    rect top-left as origin and their facing direction.  This circle is fixed at
    spawn (Phase 0: static hitbox — it does not follow the owner once launched).
    combat.process_hits uses this circle for hit detection instead of the rect.
    The rect is kept for rendering only, centered on the circle.
    """

    COLOR = (255, 60, 60, 180)  # semi-transparent red

    def __init__(
        self,
        owner,
        hitbox,             # Hitbox dataclass (circle, damage, angle, knockback)
        lifetime: int,      # frames the hit-box persists (a move's active window)
        disappear_on_hit=False,
    ):
        super().__init__()
        self.owner = owner
        self.disappear_on_hit = disappear_on_hit
        self.active = True

        # lifetime: how many frames the hit-box persists. Task 4 spawns the
        # hit-box during a move's active window with lifetime == move.active.
        self.frames_left = lifetime

        # ---------- hitbox circle (Task 5) ----------
        # Resolve the move's facing-relative circle to an absolute center ONCE at
        # spawn from the owner's current position (Phase 0: static hitbox).
        # Origin convention: owner.rect top-left (rect.x, rect.y).
        self.damage = hitbox.damage
        self.angle = hitbox.angle
        self.base_knockback = hitbox.base_knockback
        self.knockback_growth = hitbox.knockback_growth
        hit_cx, hit_cy, hit_r = resolve_circle(
            hitbox.circle,
            owner.rect.x,
            owner.rect.y,
            owner.facing_right,
        )

        self.hit_cx: float = hit_cx
        self.hit_cy: float = hit_cy
        self.hit_r: float = hit_r

        # ---------- rendering rect (kept for visuals only) ----------
        # Centre the rect on the resolved circle so the drawn box tracks the
        # hitbox position, regardless of how it was constructed.
        self.image = pygame.Surface(ATTACK_SIZE, pygame.SRCALPHA)
        self.image.fill(self.COLOR)
        self.rect = self.image.get_rect(center=(int(hit_cx), int(hit_cy)))

    # called every frame by sprite.Group.update()
    def update(self):
        self.frames_left -= 1
        if self.frames_left <= 0:
            self.kill()
