#!/usr/bin/env python3
"""Test script to compare left vs right dodge behavior."""

import pygame as pg
from pycats.entities.player import Player
from pycats.entities.platform import Platform
from pycats.core.input import InputFrame

pg.init()

# Create a large thick platform to avoid edge issues
platforms = [
    Platform(pg.Rect(100, 400, 600, 30), False),  # Wide thick platform
]


def test_dodge_direction(direction_name, direction_key, dir_x):
    print(f"\n=== Testing {direction_name} Dodge ===")

    # Create player in center of platform
    controls = {
        "left": pg.K_a,
        "right": pg.K_d,
        "up": pg.K_w,
        "down": pg.K_s,
        "shield": pg.K_q,
        "attack": pg.K_e,
    }
    player = Player(
        400, 370, controls, (255, 160, 64), (255, 255, 255), f"{direction_name}Cat"
    )

    # Settle on platform
    settle_frame = InputFrame(held=set(), pressed=set(), released=set())
    player.update(settle_frame, platforms, pg.sprite.Group())

    start_pos = player.rect.center[0]
    print(f"Start position: x={start_pos}, on_ground={player.on_ground}")

    # Trigger dodge
    dodge_frame = InputFrame(
        held={direction_key},  # Direction held
        pressed={direction_key},  # Direction just pressed
        released=set(),
    )

    player.update(dodge_frame, platforms, pg.sprite.Group())
    print(
        f"After dodge trigger: state={player.fsm.state}, vel={player.vel}, dodge_timer={player.dodge_timer}"
    )

    # Track movement for several frames
    positions = [start_pos]
    velocities = [player.vel.x]

    for frame in range(1, 15):  # DODGE_TIME is 14
        continue_frame = InputFrame(held={direction_key}, pressed=set(), released=set())
        player.update(continue_frame, platforms, pg.sprite.Group())

        current_x = player.rect.center[0]
        positions.append(current_x)
        velocities.append(player.vel.x)

        if frame <= 3 or frame >= 12:  # Show early and late frames
            print(
                f"Frame {frame}: x={current_x}, vel={player.vel}, state={player.fsm.state}, timer={player.dodge_timer}"
            )

    final_pos = player.rect.center[0]
    total_distance = final_pos - start_pos
    expected_distance = dir_x * 22 * 14  # DODGE_SPEED * DODGE_TIME

    print(f"Total distance: {total_distance} (expected: {expected_distance})")
    print(
        f"Distance ratio: {total_distance / expected_distance if expected_distance != 0 else 'N/A'}"
    )

    # Check if velocity was consistent
    dodge_velocities = [
        v for v in velocities[1:] if v != 0
    ]  # Skip initial and zero velocities
    if dodge_velocities:
        avg_vel = sum(dodge_velocities) / len(dodge_velocities)
        print(f"Average dodge velocity: {avg_vel:.1f} (expected: {dir_x * 22})")

    return total_distance, velocities


# Test both directions
right_distance, right_vels = test_dodge_direction("Right", pg.K_d, 1)
left_distance, left_vels = test_dodge_direction("Left", pg.K_a, -1)

print(f"\n=== Comparison ===")
print(f"Right dodge distance: {right_distance}")
print(f"Left dodge distance: {left_distance}")
print(f"Distance difference: {abs(right_distance) - abs(left_distance)}")

# Check for velocity pattern differences
print(f"\nRight velocities (first 5): {right_vels[:5]}")
print(f"Left velocities (first 5): {left_vels[:5]}")

pg.quit()
