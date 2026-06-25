#!/usr/bin/env python3
"""Test script to verify air dodge horizontal velocity behavior."""

import pygame as pg
import sys

sys.path.append(".")

from pycats.entities.player import Player
from pycats.entities.platform import Platform
from pycats.core.input import InputFrame
from pycats.config import DODGE_SPEED, DODGE_TIME


def test_air_dodge_velocity():
    pg.init()

    # Create platform for reference but start player in air
    platforms = [Platform(pg.Rect(200, 500, 400, 30), False)]

    print("=== Testing Air Dodge Horizontal Velocity ===")
    print(f"DODGE_SPEED = {DODGE_SPEED}, DODGE_TIME = {DODGE_TIME}")

    def test_air_dodge_direction(direction_name, direction_key, expected_vel_x):
        print(f"\n--- {direction_name} Air Dodge ---")

        controls = {
            "left": pg.K_a,
            "right": pg.K_d,
            "up": pg.K_w,
            "down": pg.K_s,
            "shield": pg.K_q,
            "attack": pg.K_e,
        }
        player = Player(
            400,
            300,
            controls,
            (255, 160, 64),
            (255, 255, 255),
            f"{direction_name}AirCat",
        )

        # Let player fall a bit to ensure in air
        for i in range(3):
            fall_frame = InputFrame(held=set(), pressed=set(), released=set())
            player.update(fall_frame, platforms, pg.sprite.Group())

        print(
            f"Before air dodge: pos={player.rect.center}, on_ground={player.on_ground}, vel={player.vel}"
        )

        # Trigger air dodge (shield + direction simultaneously)
        air_dodge_frame = InputFrame(
            held={pg.K_q, direction_key},
            pressed={pg.K_q, direction_key},
            released=set(),
        )

        start_pos = player.rect.centerx
        player.update(air_dodge_frame, platforms, pg.sprite.Group())

        print(f"After air dodge trigger: state={player.fsm.state}, vel={player.vel}")
        print(f"Expected vel.x: {expected_vel_x}, Actual vel.x: {player.vel.x}")

        # Continue for several frames to see movement
        continue_frame = InputFrame(
            held={pg.K_q, direction_key}, pressed=set(), released=set()
        )

        for frame in range(5):
            player.update(continue_frame, platforms, pg.sprite.Group())
            if frame == 0:
                print(f"Frame 1: pos={player.rect.center}, vel={player.vel}")
            elif frame == 4:
                print(f"Frame 5: pos={player.rect.center}, vel={player.vel}")

        final_pos = player.rect.centerx
        distance = final_pos - start_pos
        expected_distance = expected_vel_x * 5  # 5 frames of movement

        print(
            f"Distance moved in 5 frames: {distance}px (expected: {expected_distance}px)"
        )

        # Check if velocity is correct
        velocity_correct = abs(player.vel.x - expected_vel_x) < 0.1
        movement_correct = abs(distance - expected_distance) < 5

        if velocity_correct and movement_correct:
            print(f"✅ {direction_name} air dodge working correctly")
        else:
            print(f"❌ {direction_name} air dodge has issues:")
            if not velocity_correct:
                print(
                    f"   - Velocity incorrect: got {player.vel.x}, expected {expected_vel_x}"
                )
            if not movement_correct:
                print(
                    f"   - Movement incorrect: got {distance}, expected {expected_distance}"
                )

        return velocity_correct and movement_correct

    # Test air dodge without direction (should have no horizontal velocity)
    print("\n--- No Direction Air Dodge ---")
    controls = {
        "left": pg.K_a,
        "right": pg.K_d,
        "up": pg.K_w,
        "down": pg.K_s,
        "shield": pg.K_q,
        "attack": pg.K_e,
    }
    player_neutral = Player(
        400, 300, controls, (128, 128, 255), (255, 255, 255), "NeutralAirCat"
    )

    # Let player fall a bit
    for i in range(3):
        fall_frame = InputFrame(held=set(), pressed=set(), released=set())
        player_neutral.update(fall_frame, platforms, pg.sprite.Group())

    print(f"Before neutral air dodge: vel={player_neutral.vel}")

    # Trigger neutral air dodge (shield only)
    neutral_air_dodge_frame = InputFrame(
        held={pg.K_q}, pressed={pg.K_q}, released=set()
    )

    player_neutral.update(neutral_air_dodge_frame, platforms, pg.sprite.Group())
    print(
        f"After neutral air dodge: state={player_neutral.fsm.state}, vel={player_neutral.vel}"
    )
    print(f"Expected vel.x: 0, Actual vel.x: {player_neutral.vel.x}")

    # Test directional air dodges
    right_correct = test_air_dodge_direction("Right", pg.K_d, DODGE_SPEED)
    left_correct = test_air_dodge_direction("Left", pg.K_a, -DODGE_SPEED)

    neutral_correct = abs(player_neutral.vel.x) < 0.1

    print(f"\n=== Air Dodge Test Results ===")
    print(f"Neutral air dodge (no direction): {'✅' if neutral_correct else '❌'}")
    print(f"Right air dodge: {'✅' if right_correct else '❌'}")
    print(f"Left air dodge: {'✅' if left_correct else '❌'}")

    if neutral_correct and right_correct and left_correct:
        print("\n🎉 All air dodge tests passed!")
    else:
        print(
            "\n⚠️  Some air dodge tests failed - horizontal velocity may not be working correctly"
        )

    pg.quit()


if __name__ == "__main__":
    test_air_dodge_velocity()
