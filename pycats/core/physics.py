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


def solve_horizontal(actor: pg.Rect, vel: pg.Vector2, platforms) -> pg.Vector2:
    """Resolve horizontal collisions against the SIDE faces of solid platforms.

    Issue #5 / Project M fidelity: a *thick* platform is solid on all sides, so
    a side face blocks entry; a *thin* platform is a one-way floor you pass
    through from the sides (and from below), so it is skipped here.

    Disambiguates a genuine side entry from a top-landing using the pre-move
    horizontal edge (`actor.right - vel.x`), mirroring how `solve_vertical`
    uses `actor.bottom - vel.y`. Mutates `actor` in place; returns `vel`.
    """
    for p in platforms:
        if p.thin:
            continue  # soft platforms stay pass-through on their sides
        if not actor.colliderect(p.rect):
            continue
        if vel.x > 0 and actor.right - vel.x <= p.rect.left:
            # moving right, was clear of the left face before the move
            actor.right = p.rect.left
            vel.x = 0
        elif vel.x < 0 and actor.left - vel.x >= p.rect.right:
            # moving left, was clear of the right face before the move
            actor.left = p.rect.right
            vel.x = 0
    return vel


# ----------------------------------------------------------------- horizontal


def apply_horizontal_friction(
    vel: pg.Vector2, on_ground: bool, factor_ground: float = GROUND_FRICTION
) -> pg.Vector2:
    """
    Multiply vel.x by ground- or air-friction factor.
    """
    factor = factor_ground if on_ground else AIR_FRICTION
    vel.x *= factor  # no rounding
    if abs(vel.x) < 0.05:  # dead-zone
        vel.x = 0
    return vel


# -------------------------------------------------- player-to-player collision
def resolve_player_push(players: list["Player"]) -> None:
    for i in range(len(players)):
        for j in range(i + 1, len(players)):
            a, b = players[i], players[j]

            # Skip players in "dodge" state
            if a.state == "dodge" or b.state == "dodge":
                continue
            if not a.rect.colliderect(b.rect):
                continue

            # Issue #1 / Project M "jostle": fighter-vs-fighter collision is
            # resolved on the X axis ONLY. Push the players apart horizontally;
            # never block or reposition them on Y — vertical overlap between
            # fighters is allowed (one may briefly stand on another's head, then
            # be nudged off sideways). Player-vs-PLATFORM vertical collision is a
            # separate concern handled by solve_vertical.
            if a.rect.centerx < b.rect.centerx:  # A is to the left of B
                overlap = a.rect.right - b.rect.left
                # Move both players away from each other equally
                a.rect.x -= overlap // 2 + 1
                b.rect.x += overlap // 2 + 1
            else:  # B is to the left of A (also the perfectly-stacked tie-break)
                overlap = b.rect.right - a.rect.left
                a.rect.x += overlap // 2 + 1
                b.rect.x -= overlap // 2 + 1

            # Pushing logic — match velocities so neither side gains an advantage
            if (a.vel.x > 0 and b.vel.x < 0) or (a.vel.x < 0 and b.vel.x > 0):
                # Pushing in opposite directions — cancel out
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
            # If both move the same direction, average them
            elif a.vel.x != 0 and b.vel.x != 0:
                avg = (a.vel.x + b.vel.x) / 2
                a.vel.x = avg
                b.vel.x = avg


# ----------------------------------------------------------------- edge detection for dodging


def find_current_platform(actor_rect: pg.Rect, platforms):
    """
    Find which platform the actor is currently standing on.

    Args:
        actor_rect: Current position of the actor
        platforms: List of all platforms

    Returns:
        The platform the actor is standing on, or None if not on any platform
    """
    for platform in platforms:
        platform_rect = platform.rect
        # Check if actor is standing on this platform
        # Allow small tolerance for floating point precision
        bottom_tolerance = 2
        if (
            abs(actor_rect.bottom - platform_rect.top) <= bottom_tolerance
            and actor_rect.right > platform_rect.left
            and actor_rect.left < platform_rect.right
        ):
            return platform
    return None


def would_dodge_off_platform(
    actor_rect: pg.Rect, dodge_velocity: float, current_platform
) -> bool:
    """
    Check if a dodge with the given velocity would take the actor off their current platform.

    Args:
        actor_rect: Current position of the actor
        dodge_velocity: The horizontal velocity of the dodge (can be positive or negative)
        current_platform: The platform the actor is standing on

    Returns:
        True if the dodge would take the actor off the platform, False otherwise
    """
    if current_platform is None or dodge_velocity == 0:
        return False

    platform_rect = current_platform.rect

    # Calculate where the actor would be after this frame's movement
    future_rect = actor_rect.copy()
    future_rect.x += dodge_velocity

    # We want to prevent the player from going completely off the platform
    # Check if enough of the player would remain on the platform
    min_overlap = 25  # Require at least 25 pixels of overlap to stay safe

    if dodge_velocity > 0:  # Moving right
        # Check if there would still be enough overlap on the right side
        overlap_after_move = platform_rect.right - future_rect.left
        return overlap_after_move < min_overlap
    else:  # Moving left (dodge_velocity < 0)
        # Check if there would still be enough overlap on the left side
        overlap_after_move = future_rect.right - platform_rect.left
        return overlap_after_move < min_overlap
