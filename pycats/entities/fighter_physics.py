"""
pycats/entities/fighter_physics.py

step_physics — the per-frame physics orchestration for a fighter (#77 / D1 slice
4), lifted out of Player.update(). Applies gravity, the edge-aware dodge
clamping, movement, thin-platform drop-through prevention, and vertical /
horizontal collision via the pure core.physics primitives, then resets jumps on
landing. Mutates the passed Player; behaviour is verbatim the old update() block.

Platforms is passed in (not stashed on the entity), so the old
`self.platforms` / `hasattr(self, "platforms")` dance is gone.
"""
from ..core.physics import (
    apply_gravity,
    move_rect,
    solve_vertical,
    solve_horizontal,
    find_current_platform,
    would_dodge_off_platform,
)


def step_physics(p, platforms, held):
    """Advance fighter ``p``'s physics one frame against ``platforms``.

    ``held`` is the held-keys set (for the shield+down drop-through guard).
    """
    was_airborne = not p.on_ground

    # Apply gravity - but not for ground-based spot dodges to prevent falling
    # through thin platforms. Air dodges should still have normal gravity.
    is_ground_spot_dodge = (
        p.state == "dodge" and p.spot_dodge_shield_held and p.on_ground
    )
    if not is_ground_spot_dodge:
        apply_gravity(p.vel)
    else:
        # For ground spot dodges, keep velocity minimal to prevent any fall-through
        p.vel.y = 0

    # Edge-aware dodge: prevent horizontal movement if it would take the player
    # off the platform. After friction, immediately before movement.
    if p.state == "dodge" and p.on_ground:
        current_platform = find_current_platform(p.rect, platforms)
        if current_platform is not None:
            # First, check if velocity would take us off edge.
            if p.vel.x != 0 and would_dodge_off_platform(
                p.rect, p.vel.x, current_platform
            ):
                p.vel.x = 0
                p.dodge_blocked_by_edge = True

            # Second, clamp position so the player never goes past platform edges
            # (safety net in case any movement still occurs).
            platform_rect = current_platform.rect
            if p.rect.left < platform_rect.left:
                p.rect.left = platform_rect.left
                p.vel.x = 0  # Stop any leftward movement
            if p.rect.right > platform_rect.right:
                p.rect.right = platform_rect.right
                p.vel.x = 0  # Stop any rightward movement

    # Apply movement - this must happen immediately after the edge check.
    move_rect(p.rect, p.vel)

    # Post-movement clamping: ensure the dodge didn't move the player off-platform.
    if p.state == "dodge" and p.on_ground:
        current_platform = find_current_platform(p.rect, platforms)
        if current_platform is not None:
            platform_rect = current_platform.rect
            if p.rect.left < platform_rect.left:
                p.rect.left = platform_rect.left
                p.vel.x = 0
            if p.rect.right > platform_rect.right:
                p.rect.right = platform_rect.right
                p.vel.x = 0

    # Prevent drop-through of thin platforms when shield is held with down (both
    # during a ground spot dodge and in shield state).
    is_shield_down_held = p._pressed(held, "shield") and p._pressed(held, "down")
    should_prevent_drop_through = (
        (p.state == "dodge" and p.spot_dodge_shield_held)
        or (p.state == "shield" and is_shield_down_held)
    )

    p.vel, p.on_ground, p.drop_platform = solve_vertical(
        p.rect,
        p.vel,
        platforms,
        p._pressed(held, "down") and not should_prevent_drop_through,
        p.drop_platform,
    )

    # Issue #5: block the SIDE faces of solid (thick) platforms. Runs after
    # solve_vertical so a top-landing is resolved first and not mistaken for a
    # side entry.
    p.vel = solve_horizontal(p.rect, p.vel, platforms)

    # Maintain on_ground during a ground spot dodge to prevent unwanted fall
    # transitions.
    if p.state == "dodge" and p.spot_dodge_shield_held:
        if not p.on_ground:
            p.on_ground = True
            current_platform = find_current_platform(p.rect, platforms)
            if current_platform:
                p.rect.bottom = current_platform.rect.top

    p._handle_landing(was_airborne)
