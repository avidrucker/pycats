#!/usr/bin/env python3
"""Comprehensive dodge test with wide platform for both idle and shield state transitions."""

try:
    import pygame as pg
    import sys
    import os

    # Add parent directory to path for imports
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from pycats.entities.player import Player
    from pycats.entities.platform import Platform
    from pycats.core.input import InputFrame
    from pycats.config import DODGE_SPEED, DODGE_TIME

    print("Starting dodge tests...")
    pg.init()

    # Create very wide platform - 800px wide to ensure no edge issues
    platforms = [Platform(pg.Rect(100, 400, 800, 30), False)]
    print(f"Platform: x=100-900, y=400, width=800px")
    print(f"DODGE_SPEED={DODGE_SPEED}, DODGE_TIME={DODGE_TIME}")

    def test_dodge(test_name, start_in_shield, direction, dir_key):
        print(f"\n=== {test_name} ===")

        # Create player at center of wide platform (x=500) and ON the platform
        controls = {
            "left": pg.K_a,
            "right": pg.K_d,
            "up": pg.K_w,
            "down": pg.K_s,
            "shield": pg.K_q,
            "attack": pg.K_e,
        }
        player = Player(
            500,
            400,
            controls,
            (255, 160, 64),
            (255, 255, 255),
            test_name.replace(" ", ""),
        )

        # Settle on platform
        settle = InputFrame(held=set(), pressed=set(), released=set())
        player.update(settle, platforms, pg.sprite.Group())
        print(
            f"Settled: pos={player.rect.center}, on_ground={player.on_ground}, state={player.fsm.state}"
        )

        # Enter shield state if needed
        if start_in_shield:
            shield_frame = InputFrame(held={pg.K_q}, pressed={pg.K_q}, released=set())
            player.update(shield_frame, platforms, pg.sprite.Group())
            print(f"Shield state: {player.fsm.state}")

        # Record starting position
        start_x = player.rect.centerx

        # Trigger dodge
        if start_in_shield:
            # From shield: add direction to existing shield
            dodge_frame = InputFrame(
                held={pg.K_q, dir_key},
                pressed={dir_key},  # Only direction is newly pressed
                released=set(),
            )
        else:
            # From idle: press shield + direction simultaneously
            dodge_frame = InputFrame(
                held={pg.K_q, dir_key},
                pressed={pg.K_q, dir_key},  # Both newly pressed
                released=set(),
            )

        player.update(dodge_frame, platforms, pg.sprite.Group())
        print(
            f"After trigger: state={player.fsm.state}, vel={player.vel}, timer={player.dodge_timer}"
        )

        # Run full dodge duration
        continue_frame = InputFrame(
            held={pg.K_q, dir_key}, pressed=set(), released=set()
        )

        for frame in range(DODGE_TIME):
            player.update(continue_frame, platforms, pg.sprite.Group())
            if frame == 0:
                print(f"Frame 1: pos={player.rect.center}, vel={player.vel}")
            elif frame == DODGE_TIME - 1:
                print(f"Frame {DODGE_TIME}: pos={player.rect.center}, vel={player.vel}")

        # Calculate distance
        final_x = player.rect.centerx
        distance = final_x - start_x
        expected = direction * DODGE_SPEED * DODGE_TIME

        print(f"Distance: {distance}px (expected: {expected}px)")
        print(f"Final state: {player.fsm.state}")

        return distance

    # Test all 4 combinations
    results = {}

    results["idle_right"] = test_dodge("Idle to Right Dodge", False, 1, pg.K_d)
    results["idle_left"] = test_dodge("Idle to Left Dodge", False, -1, pg.K_a)
    results["shield_right"] = test_dodge("Shield to Right Dodge", True, 1, pg.K_d)
    results["shield_left"] = test_dodge("Shield to Left Dodge", True, -1, pg.K_a)

    # Summary
    print(f"\n=== RESULTS SUMMARY ===")
    print(f"Expected distance per dodge: {DODGE_SPEED * DODGE_TIME}px")

    for key, distance in results.items():
        state, direction = key.split("_")
        print(f"{state.capitalize()} {direction}: {distance}px")

    # Check for issues
    print(f"\n=== ISSUE ANALYSIS ===")

    # Check idle symmetry
    idle_diff = abs(results["idle_right"]) - abs(results["idle_left"])
    if abs(idle_diff) > 5:
        print(
            f"❌ IDLE ASYMMETRY: Right={results['idle_right']}, Left={results['idle_left']}, Diff={idle_diff}"
        )
    else:
        print(f"✅ Idle dodges symmetric")

    # Check shield symmetry
    shield_diff = abs(results["shield_right"]) - abs(results["shield_left"])
    if abs(shield_diff) > 5:
        print(
            f"❌ SHIELD ASYMMETRY: Right={results['shield_right']}, Left={results['shield_left']}, Diff={shield_diff}"
        )
    else:
        print(f"✅ Shield dodges symmetric")

    # Check idle vs shield consistency
    right_consistency = abs(results["idle_right"] - results["shield_right"])
    left_consistency = abs(abs(results["idle_left"]) - abs(results["shield_left"]))

    if right_consistency > 5:
        print(
            f"❌ RIGHT INCONSISTENCY: Idle={results['idle_right']}, Shield={results['shield_right']}, Diff={right_consistency}"
        )
    else:
        print(f"✅ Right dodge consistent between states")

    if left_consistency > 5:
        print(
            f"❌ LEFT INCONSISTENCY: Idle={abs(results['idle_left'])}, Shield={abs(results['shield_left'])}, Diff={left_consistency}"
        )
    else:
        print(f"✅ Left dodge consistent between states")

    pg.quit()
    print("Test completed successfully")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback

    traceback.print_exc()
