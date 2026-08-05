# pycats/systems/movement.py

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pg is used only in (stringized) annotations — never at runtime,
    import pygame as pg  # type: ignore  # so this module carries no import-time pygame dep (#975, ADR-0004).

from ..core.physics import apply_horizontal_friction


def step_horizontal(
    vel: pg.Vector2,
    facing_right: bool,
    on_ground: bool,
    press_left: bool,
    press_right: bool,
    locked: bool = False,
    *,
    move_speed: float,
) -> tuple[pg.Vector2, bool]:
    """
    • Applies friction (ground or air) first.
    • If BOTH left & right are pressed → inputs cancel out.
    • Returns (new_vel, new_facing_right).

    move_speed is per-fighter (#126) and REQUIRED (keyword-only): the config
    MOVE_SPEED global was removed in the ADR-0011 re-pin (#1209), so a caller must
    pass the fighter's shipped px (walk/dash/run selected by state upstream).
    """
    # 1) friction
    vel = apply_horizontal_friction(vel, on_ground)

    # 2) cancel out opposite inputs
    if press_left and press_right:
        return vel, facing_right

    if not locked:
        if press_left:
            vel.x = -move_speed
            facing_right = False
        elif press_right:
            vel.x = move_speed
            facing_right = True

    return vel, facing_right
