# pycats/core/physics.py

#### TODO: prevent all collisions with thick platforms, including horizontal (from the side) and upwards vertical

from __future__ import annotations

from typing import Tuple, Optional
import pygame as pg  # type: ignore

# Read tuning constants from config once
from ..config import (
    GRAVITY,
    MAX_FALL_SPEED,
    GROUND_FRICTION,
    AIR_FRICTION,
)

# ------------------------------------------------------------------ vertical


def apply_gravity(vel: pg.Vector2) -> pg.Vector2:
    """
    Add gravity but never let velocity exceed MAX_FALL_SPEED.
    Returns the *same* Vector2 (mutated) for chaining.
    """
    vel.y = min(vel.y + GRAVITY, MAX_FALL_SPEED)
    return vel


def move_rect(rect: pg.Rect, vel: pg.Vector2) -> None:
    """Translate rect by vel (in-place)."""
    rect.x += vel.x
    rect.y += vel.y


def solve_vertical(
    actor: pg.Rect,
    vel: pg.Vector2,
    platforms,
    press_down: bool,
    drop_platform: Optional[pg.sprite.Sprite],
) -> Tuple[pg.Vector2, bool, Optional[pg.sprite.Sprite]]:
    """
    Resolve vertical collisions against a list of platforms.

    Returns (new_vel, on_ground, new_drop_platform)
    Pure maths: no Player-specific references.
    """
    on_ground = False
    new_drop = drop_platform

    if drop_platform and actor.top > drop_platform.rect.bottom:
        new_drop = None  # we fell through it

    def x_overlap(a: pg.Rect, b: pg.Rect) -> bool:
        return a.right > b.left and a.left < b.right

    landing = None
    for p in platforms:
        if p is new_drop:
            continue

        overlap = actor.colliderect(p.rect)
        flush = actor.bottom == p.rect.top and vel.y >= 0 and x_overlap(actor, p.rect)
        if not (overlap or flush):
            continue

        if p.thin:
            from_above = vel.y >= 0 and actor.bottom - vel.y <= p.rect.top
            if from_above and not press_down:
                landing = p
        else:
            if vel.y >= 0 and actor.bottom - vel.y <= p.rect.top:
                landing = p
            elif vel.y < 0 and actor.top - vel.y >= p.rect.bottom:
                actor.top = p.rect.bottom
                vel.y = 0

    if landing:
        actor.bottom = landing.rect.top
        vel.y = 0
        on_ground = True
        if landing.thin and press_down:
            new_drop = landing

    return vel, on_ground, new_drop


# ----------------------------------------------------------------- horizontal


def apply_horizontal_friction(
    vel: pg.Vector2, on_ground: bool, factor_ground: float = GROUND_FRICTION
) -> pg.Vector2:
    """
    Multiply vel.x by ground- or air-friction factor.
    """
    factor = factor_ground if on_ground else AIR_FRICTION
    vel.x *= factor                # no rounding
    if abs(vel.x) < 0.05:          # dead-zone
        vel.x = 0
    return vel


# -------------------------------------------------- player-to-player collision
def resolve_player_push(players: list["Player"]) -> None:
    for i in range(len(players)):
        for j in range(i + 1, len(players)):
            a, b = players[i], players[j]
            
            # Skip players in "dodge" state
            if a.fsm.state == "dodge" or b.fsm.state == "dodge":
                continue
            if not a.rect.colliderect(b.rect):
                continue

            # Calculate overlap on each axis
            dx_left = a.rect.right - b.rect.left
            dx_right = b.rect.right - a.rect.left
            dy_top = a.rect.bottom - b.rect.top
            dy_bot = b.rect.bottom - a.rect.top

            # Determine which axis has the smaller overlap
            dx = min(dx_left, dx_right)
            dy = min(dy_top, dy_bot)
            
            if dx < dy:  # Resolve horizontally
                # Calculate the overlap amount
                if a.rect.centerx < b.rect.centerx:  # A is to the left of B
                    overlap = (a.rect.right - b.rect.left)
                    # Move both players away from each other equally
                    a.rect.x -= overlap // 2 + 1
                    b.rect.x += overlap // 2 + 1
                else:  # B is to the left of A
                    overlap = (b.rect.right - a.rect.left)
                    a.rect.x += overlap // 2 + 1
                    b.rect.x -= overlap // 2 + 1

                # Pushing logic
                # Exactly match velocities and directions to prevent one side gaining advantage
                if (a.vel.x > 0 and b.vel.x < 0) or (a.vel.x < 0 and b.vel.x > 0):
                    # They're pushing in opposite directions - completely cancel out
                    a.vel.x = 0.0
                    b.vel.x = 0.0
                # If only one is pushing, both move at half the pusher's speed
                elif a.vel.x != 0 and b.vel.x == 0:
                    push_speed = a.vel.x * 0.5
                    a.vel.x = push_speed
                    b.vel.x = push_speed
                elif b.vel.x != 0 and a.vel.x == 0:
                    push_speed = b.vel.x * 0.5
                    a.vel.x = push_speed
                    b.vel.x = push_speed
                # If both are moving in the same direction, keep their velocities (optional: average them)
                elif a.vel.x != 0 and b.vel.x != 0:
                    avg = (a.vel.x + b.vel.x) / 2
                    a.vel.x = avg
                    b.vel.x = avg
            else:  # Resolve vertically
                # Special handling for vertical collisions:
                # 1. For player jump-on-player, don't push them through platforms
                a_on_ground = getattr(a, "on_ground", False)
                b_on_ground = getattr(b, "on_ground", False)
                
                # If either player is on ground, don't move them down
                if a.rect.centery < b.rect.centery:  # A is above B
                    overlap = (a.rect.bottom - b.rect.top)
                    # If B is on ground, only move A up
                    if b_on_ground:
                        a.rect.bottom = b.rect.top - 1
                    else:
                        # Otherwise share the separation
                        a.rect.y -= overlap // 2 + 1
                        b.rect.y += overlap // 2 + 1
                else:  # B is above A
                    overlap = (b.rect.bottom - a.rect.top)
                    # If A is on ground, only move B up
                    if a_on_ground:
                        b.rect.bottom = a.rect.top - 1
                    else:
                        # Otherwise share the separation
                        a.rect.y += overlap // 2 + 1
                        b.rect.y -= overlap // 2 + 1

                # Pushing logic for vertical - more restrictive
                # Complete cancellation of vertical velocities when pushing against each other
                if (a.vel.y > 0 and b.vel.y < 0) or (a.vel.y < 0 and b.vel.y > 0):
                    a.vel.y = 0.0
                    b.vel.y = 0.0
                # If on ground, can't be pushed down
                elif a_on_ground and b.vel.y > 0:
                    a.vel.y = 0.0
                    b.vel.y = 0.0
                elif b_on_ground and a.vel.y > 0:
                    a.vel.y = 0.0
                    b.vel.y = 0.0
                # For other cases, use limited push
                elif a.vel.y != 0 and b.vel.y == 0:
                    # Limit downward pushing
                    if a.vel.y > 0 and b_on_ground:
                        a.vel.y = 0
                    else:
                        push_speed = a.vel.y * 0.5
                        a.vel.y = push_speed
                        b.vel.y = push_speed
                elif b.vel.y != 0 and a.vel.y == 0:
                    # Limit downward pushing
                    if b.vel.y > 0 and a_on_ground:
                        b.vel.y = 0
                    else:
                        push_speed = b.vel.y * 0.5
                        a.vel.y = push_speed
                        b.vel.y = push_speed
