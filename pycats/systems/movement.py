# pycats/systems/movement.py

import pygame as pg  # type: ignore

from ..config import MOVE_SPEED
from ..core.physics import apply_horizontal_friction


def step_horizontal(
    vel: pg.Vector2,
    facing_right: bool,
    on_ground: bool,
    press_left: bool,
    press_right: bool,
    locked: bool = False,
    move_speed: float = MOVE_SPEED,
) -> tuple[pg.Vector2, bool]:
    """
    • Applies friction (ground or air) first.
    • If BOTH left & right are pressed → inputs cancel out.
    • Returns (new_vel, new_facing_right).

    move_speed is per-fighter (#126); defaults to the config global so callers
    that don't pass it behave exactly as before.
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
