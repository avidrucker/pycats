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
from ..config import (
    ATTACK_LIFETIME,
    ATTACK_SIZE,
    HIT_DAMAGE,
    KNOCKBACK_BASE,
    KNOCKBACK_SCALE,
)
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
        hitbox=None,        # Hitbox dataclass (circle, damage, angle); preferred
        damage: int = HIT_DAMAGE,
        disappear_on_hit=False,
        base_kb=KNOCKBACK_BASE,
        kb_scale=KNOCKBACK_SCALE,
        angle=0,
        lifetime: int = ATTACK_LIFETIME,
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
        if hitbox is not None:
            self.damage = hitbox.damage
            self.angle = hitbox.angle
            hit_cx, hit_cy, hit_r = resolve_circle(
                hitbox.circle,
                owner.rect.x,
                owner.rect.y,
                owner.facing_right,
            )
        else:
            # Fallback: no Hitbox provided — derive a circle from the legacy
            # rect offset so older call-sites still work.
            self.damage = damage
            self.angle = angle
            offset_x = owner.rect.width // 2 + 4
            raw_dx = offset_x if owner.facing_right else -offset_x
            hit_cx = owner.rect.x + raw_dx + ATTACK_SIZE[0] // 2
            hit_cy = owner.rect.y + owner.rect.height // 2
            hit_r = min(ATTACK_SIZE) // 2

        self.hit_cx: float = hit_cx
        self.hit_cy: float = hit_cy
        self.hit_r: float = hit_r

        # ---------- rendering rect (kept for visuals only) ----------
        # Centre the rect on the resolved circle so the drawn box tracks the
        # hitbox position, regardless of how it was constructed.
        self.image = pygame.Surface(ATTACK_SIZE, pygame.SRCALPHA)
        self.image.fill(self.COLOR)
        self.rect = self.image.get_rect(center=(int(hit_cx), int(hit_cy)))

        self.base_kb = base_kb
        self.kb_scale = kb_scale

    # called every frame by sprite.Group.update()
    def update(self):
        self.frames_left -= 1
        if self.frames_left <= 0:
            self.kill()
