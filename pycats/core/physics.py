# pycats/core/physics.py

#### TODO: prevent all collisions with thick platforms, including horizontal (from the side) and upwards vertical

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:  # pg is used only in (stringized) annotations — never at runtime,
    import pygame as pg  # type: ignore  # so the core carries no import-time pygame dep (#968, ADR-0004).


class _DropThrough(Protocol):
    """A drop-through platform token — the physics only reads its `.rect`. Typed
    structurally so the core stays Sprite-free (ADR-0004 / #339): it needs a
    thing-with-a-rect, not pygame's Sprite."""

    rect: pg.Rect


# Read tuning constants from config once
from ..combat.units import u
from ..config import (
    AIR_FRICTION,
    GRAVITY,
    GROUND_FRICTION,
    JOSTLE_PUSH_UNITS,
    JOSTLE_TRIGGER_UNITS,
    MAX_FALL_SPEED,
)

# Physics thresholds (#446: named from inline literals).
VEL_DEADZONE = 0.05  # |vel.x| below this snaps to 0 after friction (dead-zone)

# Fighter-vs-fighter ground jostle (ADR-0012, #1020): raw Smash units authored in
# config; the integer-pixel trigger / push derive here at the units seam (ADR-0011 —
# u() rounds because the sim is integer-pixel, #80). round(6.5 × 5.4)=35, round(0.3 × 5.4)=2.
JOSTLE_TRIGGER_PX = u(JOSTLE_TRIGGER_UNITS)  # centre-distance below which the push fires
JOSTLE_PUSH_PX = u(JOSTLE_PUSH_UNITS)  # per-fighter position nudge each overlap frame

# ------------------------------------------------------------------ vertical


def apply_gravity(vel: pg.Vector2, gravity: float = GRAVITY, max_fall_speed: float = MAX_FALL_SPEED) -> pg.Vector2:
    """
    Add gravity but never let velocity exceed max_fall_speed.
    Returns the *same* Vector2 (mutated) for chaining.

    gravity / max_fall_speed are per-fighter (#126); they default to the config
    globals so callers that don't pass them behave exactly as before.
    """
    vel.y = min(vel.y + gravity, max_fall_speed)
    return vel


def move_rect(rect: pg.Rect, vel: pg.Vector2) -> None:
    """Translate rect by vel (in-place).

    pygame Rect coords are integers, so a raw ``rect.x += vel.x`` truncates the
    float toward zero. At a positive on-stage x that makes a leftward step
    ``ceil(|vel.x|)`` and a rightward step ``floor(|vel.x|)`` — a fixed 1px/frame
    leftward bias for any fractional ``vel.x`` (#949/#979). Rounding ``vel.x``
    symmetrically about zero *before* it reaches the int Rect makes left and right
    advance identically. ``round`` is sign-symmetric (half-to-even) so there is no
    residual bias even at the .5 boundary. This realizes a fighter's horizontal
    speed at the nearest integer px/frame (e.g. Gnok walk 6.48 → 6, dash
    9.72 → 10); carrying a sub-pixel remainder to preserve the exact fractional
    rate is out of scope here.

    ``vel.y`` is left truncating on purpose: the reported defect (#949) is
    horizontal, and rounding the gravity/jump-driven vertical step changes fall
    trajectories (it moves the golden sims). Whether every Rect-writing site
    should force int uniformly is the audit follow-up, not this fix.
    """
    rect.x += round(vel.x)
    rect.y += vel.y


def solve_vertical(
    actor: pg.Rect,
    vel: pg.Vector2,
    platforms,
    press_down: bool,
    drop_platform: _DropThrough | None,
) -> tuple[pg.Vector2, bool, _DropThrough | None]:
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


def apply_horizontal_friction(vel: pg.Vector2, on_ground: bool, factor_ground: float = GROUND_FRICTION) -> pg.Vector2:
    """
    Multiply vel.x by ground- or air-friction factor.
    """
    factor = factor_ground if on_ground else AIR_FRICTION
    vel.x *= factor  # no rounding
    if abs(vel.x) < VEL_DEADZONE:  # dead-zone
        vel.x = 0
    return vel


# -------------------------------------------------- player-to-player collision
def resolve_player_push(players: list[Player], platforms) -> None:  # noqa: F821  (Player is an unresolved forward-ref, lazy under `from __future__ import annotations`; not imported so core/ stays decoupled from entities)
    """PM-faithful ground jostle — a literal port of meleelight's grounded push
    (ADR-0012, #1020; schmooblidon/meleelight @ 27af171, src/physics/physics.js).

    For each pair of fighters, a gradual, **position-only** nudge apart along X when
    BOTH are grounded on the *same* platform and their centres are within
    JOSTLE_TRIGGER_PX. Each frame the pair is within range, each fighter moves
    JOSTLE_PUSH_PX px away from the other — a wide overlap separates over several
    frames, not one. Velocity is never touched (fighters keep their momentum), and Y
    is never resolved (vertical overlap between fighters is allowed — canon).

    The grounded gate makes airborne fighters neither push nor be pushed: two airborne
    fighters pass through / overlap each other, and a fighter flying *over* a grounded
    one no longer ratchets it sideways (superseding the #68 vertical-overlap gate).
    Player-vs-PLATFORM collision is a separate concern (solve_vertical/solve_horizontal).
    """
    for i in range(len(players)):
        for j in range(i + 1, len(players)):
            a, b = players[i], players[j]

            # Skip players in "dodge" state (kept from #1; meleelight's grab exemption
            # has no pycats analog — there is no fighter-vs-fighter grab).
            if a.state == "dodge" or b.state == "dodge":
                continue

            # Decision 4 — grounded + same-platform gate. meleelight pushes only when
            # both fighters are `grounded` on the identical surface (type + index);
            # pycats compares each fighter's current platform instance. Decision 5 —
            # no airborne jostle: this gate excludes the flyover by construction.
            if not (a.fighter.on_ground and b.fighter.on_ground):
                continue
            plat_a = find_current_platform(a.rect, platforms)
            plat_b = find_current_platform(b.rect, platforms)
            if plat_a is None or plat_a is not plat_b:
                continue

            # Decision 1 — trigger on horizontal centre-distance < JOSTLE_TRIGGER_PX
            # (meleelight `diff < 6.5`). This is an absolute centre-distance, less than
            # a default body width, so fighters settle slightly overlapping — canon.
            dx = a.rect.centerx - b.rect.centerx
            if abs(dx) >= JOSTLE_TRIGGER_PX:
                continue

            # Decisions 2 & 3 — gradual, position-only push: each fighter steps
            # JOSTLE_PUSH_PX px apart along X (meleelight `pos.x += sign(...) * -0.3`);
            # velocity is never rewritten. On an exact stack (dx == 0) apply a
            # deterministic tie-break so integer-pixel fighters still separate.
            if dx > 0:  # a is to the right of b
                a.rect.x += JOSTLE_PUSH_PX
                b.rect.x -= JOSTLE_PUSH_PX
            else:  # a is left of b, or exactly stacked (deterministic tie-break)
                a.rect.x -= JOSTLE_PUSH_PX
                b.rect.x += JOSTLE_PUSH_PX


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


def would_dodge_off_platform(actor_rect: pg.Rect, dodge_velocity: float, current_platform) -> bool:
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
