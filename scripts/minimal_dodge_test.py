#!/usr/bin/env python3
"""Minimal test to trace velocity changes during dodge."""

try:
    import sys

    import pygame as pg

    sys.path.append(".")

    from pycats.core.input import InputFrame
    from pycats.entities.platform import Platform
    from pycats.entities.player import Player

    pg.init()

    # Simple setup
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

    print("=== Minimal Dodge Test ===")

    # Single frame to settle
    settle = InputFrame(held=set(), pressed=set(), released=set())
    player.update(settle, platforms, pg.sprite.Group())
    print(
        f"After settle: state={player.fsm.state}, vel={player.vel}, on_ground={player.on_ground}"
    )

    # Trigger dodge
    print("\n--- Triggering Dodge ---")
    dodge_frame = InputFrame(held={pg.K_d}, pressed={pg.K_d}, released=set())
    print(f"Before update: vel={player.vel}")

    player.update(dodge_frame, platforms, pg.sprite.Group())

    print(
        f"After update: state={player.fsm.state}, vel={player.vel}, timer={player.dodge_timer}"
    )

    pg.quit()

except Exception as e:
    print(f"ERROR: {e}")
    import traceback

    traceback.print_exc()
