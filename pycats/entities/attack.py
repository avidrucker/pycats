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
#### TODO: implement attack hit-boxes that are larger for heavy characters and smaller for light characters
#### TODO: implement throw attacks that can throw the opponent off the stage, with a directional key (forward, backward, up, down), and throw attacks can only be executed while the attacker is in grabbing state and the opponent is in grabbed state
#### TODO: implement grab attacks ("pummeling") that can deal minor damage to a grabbed opponent
#### TODO: implement grab escape mechanics where the grabbed player can mash their inputs to escape sooner
#### TODO: implement ability for some attacks to hit more than one opponent

import pygame  # type: ignore
from ..config import ATTACK_SIZE  # render-only: sizes the drawn hit-box rect
from ..combat.geometry import resolve_circle


class Attack(pygame.sprite.Sprite):
    """Simple rectangular hit-box that disappears after N frames, and that can either vanish on hit or persist visually.

    Task 5: Attack carries absolute hitbox circles resolved from the move's
    Hitbox.circle(s) at spawn time using the owner's rect top-left as origin and
    their facing direction. The circles are fixed at spawn (Phase 0: static
    hitbox — they do not follow the owner once launched). combat.process_hits
    uses these circles for hit detection instead of the rect; the rect is kept
    for rendering only, centred on the primary (first) circle.

    #130: a move may have MORE THAN ONE hitbox. Pass ``hitboxes=<tuple>`` for the
    full set (priority order = tuple order); ``hitbox=<one>`` stays as a single-
    box shorthand. ``self.resolved`` is the priority-ordered list of
    ``(cx, cy, r, Hitbox)`` that process_hits walks; the legacy single-circle
    fields (``hit_cx/hit_cy/hit_r`` + ``damage/angle/base_knockback/
    knockback_growth``) mirror the PRIMARY box so existing readers/renderers are
    unchanged.
    """

    COLOR = (255, 60, 60, 180)  # semi-transparent red

    def __init__(
        self,
        owner,
        hitbox=None,        # single Hitbox shorthand (circle, damage, angle, kb)
        lifetime: int = 0,  # frames the hit-box persists (a move's active window)
        disappear_on_hit=False,
        hitboxes=None,      # #130: tuple[Hitbox, ...] for a multi-hitbox move
    ):
        super().__init__()
        self.owner = owner
        self.disappear_on_hit = disappear_on_hit
        self.active = True

        # lifetime: how many frames the hit-box persists. Task 4 spawns the
        # hit-box during a move's active window with lifetime == move.active.
        self.frames_left = lifetime

        # Normalise to a non-empty tuple of hitboxes (priority order preserved).
        if hitboxes is None:
            if hitbox is None:
                raise ValueError("Attack requires hitbox= or hitboxes=")
            hitboxes = (hitbox,)
        self.hitboxes = tuple(hitboxes)

        # ---------- resolve every hitbox circle (Task 5 / #130) ----------
        # Resolve each move circle to an absolute centre ONCE at spawn from the
        # owner's current position (Phase 0: static hitboxes). Origin: owner.rect
        # top-left. self.resolved is priority-ordered (cx, cy, r, Hitbox).
        self.resolved: list[tuple[float, float, float, object]] = []
        for hb in self.hitboxes:
            cx, cy, r = resolve_circle(
                hb.circle,
                owner.rect.x,
                owner.rect.y,
                owner.fighter.facing_right,
                owner.rect.width,
            )
            self.resolved.append((cx, cy, r, hb))

        # Primary (first) box backs the legacy single-circle fields + rendering.
        prim_cx, prim_cy, prim_r, prim = self.resolved[0]
        self.damage = prim.damage
        self.angle = prim.angle
        self.base_knockback = prim.base_knockback
        self.knockback_growth = prim.knockback_growth
        self.hit_cx: float = prim_cx
        self.hit_cy: float = prim_cy
        self.hit_r: float = prim_r

        # ---------- rendering rect (kept for visuals only) ----------
        # Centre the rect on the primary resolved circle so the drawn box tracks
        # the hitbox position, regardless of how it was constructed.
        self.image = pygame.Surface(ATTACK_SIZE, pygame.SRCALPHA)
        self.image.fill(self.COLOR)
        self.rect = self.image.get_rect(center=(int(prim_cx), int(prim_cy)))

    # called every frame by sprite.Group.update()
    def update(self):
        self.frames_left -= 1
        if self.frames_left <= 0:
            self.kill()
