#!/usr/bin/env python3
"""Debug test to isolate velocity issue."""

try:
    import pygame as pg
    import sys

    sys.path.append(".")

    from pycats.entities.player import Player
    from pycats.entities.platform import Platform
    from pycats.core.input import InputFrame
    from pycats.config import DODGE_SPEED

    pg.init()

    # Create very wide platform and let player settle properly
    platforms = [Platform(pg.Rect(0, 400, 1000, 30), False)]

    controls = {
        "left": pg.K_a,
        "right": pg.K_d,
        "up": pg.K_w,
        "down": pg.K_s,
        "shield": pg.K_q,
        "attack": pg.K_e,
    }
    player = Player(500, 400, controls, (255, 160, 64), (255, 255, 255), "TestCat")

    print(f"DODGE_SPEED = {DODGE_SPEED}")
    print(
        f"Initial: pos={player.rect.center}, on_ground={player.on_ground}, state={player.fsm.state}"
    )

    # Let player settle for multiple frames
    settle = InputFrame(held=set(), pressed=set(), released=set())
    for i in range(10):
        player.update(settle, platforms, pg.sprite.Group())
        if i == 9:  # Last frame
            print(
                f"After settling: pos={player.rect.center}, on_ground={player.on_ground}, state={player.fsm.state}"
            )

    # Now try right dodge from idle
    print("\n--- Right Dodge from Idle ---")
    dodge_frame = InputFrame(
        held={pg.K_q, pg.K_d}, pressed={pg.K_q, pg.K_d}, released=set()
    )

    print(f"Before dodge: vel={player.vel}")
    player.update(dodge_frame, platforms, pg.sprite.Group())
    print(
        f"After dodge trigger: vel={player.vel}, state={player.fsm.state}, timer={player.dodge_timer}"
    )

    # Check if edge detection is active
    if hasattr(player, "dodge_blocked_by_edge"):
        print(f"Edge blocked: {player.dodge_blocked_by_edge}")

    # Check if velocity gets zeroed by edge detection
    print(f"Expected velocity: {DODGE_SPEED}")
    print(f"Actual velocity: {player.vel.x}")

    pg.quit()

except Exception as e:
    print(f"ERROR: {e}")
    import traceback

    traceback.print_exc()
