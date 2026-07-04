"""
pycats/combat/geometry.py

Purpose: Pure, dependency-free circle geometry helpers for combat resolution.

Contents:
  circle_overlap(ax, ay, ar, bx, by, br) -> bool
      True if two circles (absolute centers + radii) overlap or touch.
      Uses squared-distance vs squared-radius-sum to avoid sqrt.
      Touching (distance == r1+r2) is treated as overlap (<=).

  resolve_circle(circle, origin_x, origin_y, facing_right) -> (cx, cy, r)
      Convert a facing-RIGHT-relative Circle (dx, dy, r) to an absolute
      center given a fighter origin and facing direction.
      When facing_right is True:  cx = origin_x + circle.dx
      When facing_right is False: cx = origin_x - circle.dx  (mirrored)
      cy = origin_y + circle.dy  (unaffected by facing)
      Returns (cx, cy, circle.r).

  circles_overlap(ax, ay, ar, circle_list_abs) -> bool
      True if the circle (ax, ay, ar) overlaps ANY circle in circle_list_abs,
      where circle_list_abs is a list of already-resolved (cx, cy, r) tuples.
      Returns False for an empty list.

Design notes:
  - No pygame dependency; inputs may be ints or floats.
  - All functions are deterministic and have no side effects.
  - circle_list_abs uses plain tuples for performance; callers resolve
    facing-relative Circles with resolve_circle() before passing them in.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pycats.combat.data import Circle


def circle_overlap(ax: float, ay: float, ar: float,
                   bx: float, by: float, br: float) -> bool:
    """Return True if two absolute circles overlap (touching counts as overlap).

    Uses squared-distance comparison to avoid sqrt.

    Args:
        ax, ay: center of circle A
        ar:     radius of circle A
        bx, by: center of circle B
        br:     radius of circle B

    Returns:
        True if dist(A, B) <= ar + br, False otherwise.
    """
    dx = bx - ax
    dy = by - ay
    dist_sq = dx * dx + dy * dy
    r_sum = ar + br
    return dist_sq <= r_sum * r_sum


def resolve_circle(circle: Circle,
                   origin_x: float, origin_y: float,
                   facing_right: bool, width: float) -> tuple[float, float, float]:
    """Convert a facing-relative Circle to an absolute (cx, cy, r) triple.

    `dx`/`dy` are offsets from the fighter's top-left origin in
    facing-RIGHT-relative coordinates. When the fighter faces left the offset is
    mirrored **around the body centre** (not the left-edge origin):

        facing right: cx = origin_x + dx
        facing left:  cx = origin_x + width - dx

    so a symmetric body part (``dx == width/2``) is **facing-invariant** — a
    fighter's hurtbox does not move when it turns around — and an attack pokes
    out the side it faces (an offset ``k`` past the right edge mirrors to ``k``
    past the left edge). The earlier ``origin_x - dx`` mirror pivoted on the left
    edge, placing left-facing hurtboxes off-body toward the attacker (#64).

    Args:
        circle:       A Circle(dx, dy, r) with facing-right-relative offsets.
        origin_x:     Absolute x of the fighter origin (player rect left).
        origin_y:     Absolute y of the fighter origin (player rect top).
        facing_right: True → add dx; False → mirror around the body centre.
        width:        The fighter's body width (the mirror axis is its centre).

    Returns:
        (cx, cy, r) — absolute center coordinates and radius.
    """
    if facing_right:
        cx = origin_x + circle.dx
    else:
        cx = origin_x + width - circle.dx
    cy = origin_y + circle.dy
    return (cx, cy, circle.r)


def circles_overlap(ax: float, ay: float, ar: float,
                    circle_list_abs: list[tuple[float, float, float]]) -> bool:
    """Return True if circle (ax, ay, ar) overlaps ANY circle in circle_list_abs.

    This is the primary combat query: one hitbox circle vs a list of
    already-resolved hurtbox circles.

    Args:
        ax, ay: center of the query circle (e.g. hitbox absolute center)
        ar:     radius of the query circle
        circle_list_abs: list of (cx, cy, r) tuples (already resolved to
                         absolute coordinates via resolve_circle).

    Returns:
        True if any circle in the list overlaps; False for empty list or
        no overlap.
    """
    for bx, by, br in circle_list_abs:
        if circle_overlap(ax, ay, ar, bx, by, br):
            return True
    return False


def move_reach(fighter_data, move_key: str, body_width: float):
    """Center-relative forward reach of a fighter's move, or None if it lacks it.

    The reach an AI controller cares about is measured from the body CENTRE (the
    axis its `attack_range` compares against, `adx = |t.centerx - a.centerx|`).
    A hitbox tip, facing right, sits at `origin_x + dx + r` (see resolve_circle);
    the body centre is `origin_x + body_width/2`. So the forward reach past centre
    is `max(dx + r) - body_width/2`. Pure; no pygame. Returns None when the
    character does not define `move_key`, so callers can fall back (e.g. to the
    fixed `attack_range`) rather than crash (#285/#335).
    """
    mv = fighter_data.moves.get(move_key)
    if mv is None:
        return None
    tip = max(hb.circle.dx + hb.circle.r for hb in mv.hitboxes)
    return tip - body_width / 2
