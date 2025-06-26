# pycats/systems/movement.py
from typing import Tuple
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
) -> Tuple[pg.Vector2, bool]:
    """
    • Applies friction (ground or air) first.
    • If BOTH left & right are pressed → inputs cancel out.
    • Returns (new_vel, new_facing_right).
    """
    # 1) friction
    apply_horizontal_friction(vel, on_ground)

    # 2) cancel out opposite inputs
    if press_left and press_right:
        return vel, facing_right

    if not locked:
        if press_left:
            vel.x = -MOVE_SPEED
            facing_right = False
        elif press_right:
            vel.x = MOVE_SPEED
            facing_right = True

    return vel, facing_right
