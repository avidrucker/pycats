# pycats/core/physics.py

#### TODO: prevent all collisions with thick platforms, including horizontal (from the side) and upwards vertical

from __future__ import annotations

from typing import Tuple, Optional, Protocol
import pygame as pg  # type: ignore


class _DropThrough(Protocol):
    """A drop-through platform token — the physics only reads its `.rect`. Typed
    structurally so the core stays Sprite-free (ADR-0004 / #339): it needs a
    thing-with-a-rect, not pygame's Sprite."""
    rect: pg.Rect

# Read tuning constants from config once
from ..config import (
    GRAVITY,
    MAX_FALL_SPEED,
    GROUND_FRICTION,
    AIR_FRICTION,
    JOSTLE_MIN_VOVERLAP_FRAC,
)

# Physics thresholds (#446: named from inline literals).
VEL_DEADZONE = 0.05         # |vel.x| below this snaps to 0 after friction (dead-zone)
COLLISION_PUSH_SPLIT = 0.5  # a one-sided push shares speed: both move at half the pusher's

# ------------------------------------------------------------------ vertical


def apply_gravity(vel: pg.Vector2, gravity: float = GRAVITY,
                  max_fall_speed: float = MAX_FALL_SPEED) -> pg.Vector2:
    """
    Add gravity but never let velocity exceed max_fall_speed.
    Returns the *same* Vector2 (mutated) for chaining.

    gravity / max_fall_speed are per-fighter (#126); they default to the config
    globals so callers that don't pass them behave exactly as before.
    """
    vel.y = min(vel.y + gravity, max_fall_speed)
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
    drop_platform: Optional[_DropThrough],
) -> Tuple[pg.Vector2, bool, Optional[_DropThrough]]:
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
    if abs(vel.x) < VEL_DEADZONE:  # dead-zone
        vel.x = 0
    return vel


# -------------------------------------------------- player-to-player collision
def resolve_player_push(players: list["Player"]) -> None:  # noqa: F821  ("Player" is a string forward-ref; not imported so core/ stays decoupled from entities)
    for i in range(len(players)):
        for j in range(i + 1, len(players)):
            a, b = players[i], players[j]

            # Skip players in "dodge" state
            if a.state == "dodge" or b.state == "dodge":
                continue
            if not a.rect.colliderect(b.rect):
                continue

            # Issue #68: the jostle is a grounded-contact interaction, so only
            # apply it when the two bodies are at substantially the same level.
            # An airborne fighter passing *over* a grounded one re-overlaps each
            # rising frame with only a sliver of vertical overlap; pushing on that
            # sliver ratchets the stationary fighter sideways. Require a meaningful
            # vertical overlap (≥ JOSTLE_MIN_VOVERLAP_FRAC of the shorter body) so a
            # flyover / standing-on-a-head no longer shoves the fighter below.
            v_overlap = min(a.rect.bottom, b.rect.bottom) - max(a.rect.top, b.rect.top)
            min_overlap = JOSTLE_MIN_VOVERLAP_FRAC * min(a.rect.height, b.rect.height)
            if v_overlap < min_overlap:
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
            if (a.fighter.vel.x > 0 and b.fighter.vel.x < 0) or (a.fighter.vel.x < 0 and b.fighter.vel.x > 0):
                # Pushing in opposite directions — cancel out
                a.fighter.vel.x = 0.0
                b.fighter.vel.x = 0.0
            # If only one is pushing, both move at half the pusher's speed
            elif a.fighter.vel.x != 0 and b.fighter.vel.x == 0:
                push_speed = a.fighter.vel.x * COLLISION_PUSH_SPLIT
                a.fighter.vel.x = push_speed
                b.fighter.vel.x = push_speed
            elif b.fighter.vel.x != 0 and a.fighter.vel.x == 0:
                push_speed = b.fighter.vel.x * COLLISION_PUSH_SPLIT
                a.fighter.vel.x = push_speed
                b.fighter.vel.x = push_speed
            # If both move the same direction, average them
            elif a.fighter.vel.x != 0 and b.fighter.vel.x != 0:
                avg = (a.fighter.vel.x + b.fighter.vel.x) / 2
                a.fighter.vel.x = avg
                b.fighter.vel.x = avg


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
