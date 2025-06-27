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
    vel.x = int(vel.x * factor)
    return vel


# -------------------------------------------------- player-to-player collision
def resolve_player_push(players: list["Player"]) -> None:
    """
    Separate overlapping player rects.
    • If both are moving → split the overlap 50-50.
    • If one is still    → push the still one the full distance.
    • Works on both axes so you can slide around corners.
    """
    for i in range(len(players)):
        for j in range(i + 1, len(players)):
            a, b = players[i], players[j]
            # Dodging players have no body
            if a.fsm.state == "dodge" or b.fsm.state == "dodge":
                continue
            if not a.rect.colliderect(b.rect):
                continue

            # overlap on each axis
            dx_left = a.rect.right - b.rect.left
            dx_right = b.rect.right - a.rect.left
            dy_top = a.rect.bottom - b.rect.top
            dy_bot = b.rect.bottom - a.rect.top

            # smallest-magnitude resolution vector
            push_x, push_y = 0, 0
            if min(dx_left, dx_right) < min(dy_top, dy_bot):
                push = dx_left if dx_left < dx_right else -dx_right
                push_x = push
            else:
                push = dy_top if dy_top < dy_bot else -dy_bot
                push_y = push

            # share or assign the shove
            if a.vel.length_squared() == 0 and b.vel.length_squared() != 0:
                a.rect.move_ip(push_x, push_y)
            elif b.vel.length_squared() == 0 and a.vel.length_squared() != 0:
                b.rect.move_ip(-push_x, -push_y)
            else:
                a.rect.move_ip(push_x / 2, push_y / 2)
                b.rect.move_ip(-push_x / 2, -push_y / 2)
