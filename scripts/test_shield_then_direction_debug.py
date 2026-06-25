#!/usr/bin/env python3
"""
Focused test for shield-then-direction air dodge modification.
This test specifically debugs why pressing shield first, then direction doesn't work.
"""

import pygame
import sys
import os

# Add the parent directory to sys.path to import the game modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pycats.entities.player import Player, PState
from pycats.core.input import InputFrame
from pycats.config import DODGE_SPEED


def create_test_player():
    """Create a test player in the air"""
    controls = {
        "left": pygame.K_a,
        "right": pygame.K_d,
        "up": pygame.K_w,
        "down": pygame.K_s,
        "shield": pygame.K_SPACE,
        "attack": pygame.K_j,
    }

    # Position player in air
    player = Player(
        200, 100, controls, (255, 160, 64), (0, 0, 0), "TestCat", facing_right=True
    )
    player.vel.y = 5.0  # Give some downward velocity to simulate falling
    player.on_ground = False
    player.air_dodge_ok = True

    return player


def test_shield_then_direction_detailed():
    """Detailed test of shield-then-direction air dodge with debug output"""
    print("=== Detailed Shield-Then-Direction Air Dodge Test ===")

    player = create_test_player()
    platforms = []
    attack_group = pygame.sprite.Group()

    print(
        f"Initial state: pos=({player.rect.centerx}, {player.rect.centery}), vel=({player.vel.x}, {player.vel.y})"
    )
    print(f"on_ground={player.on_ground}, air_dodge_ok={player.air_dodge_ok}")

    # Frame 1: Press shield only
    print("\n--- FRAME 1: Press shield only ---")
    pressed1 = {pygame.K_SPACE}
    held1 = {pygame.K_SPACE}
    input_frame1 = InputFrame(pressed=pressed1, held=held1, released=set())

    player.update(input_frame1, platforms, attack_group)

    print(
        f"After shield press: pos=({player.rect.centerx}, {player.rect.centery}), vel=({player.vel.x}, {player.vel.y})"
    )
    print(f"State: {player.fsm.state}, dodge_timer: {player.dodge_timer}")
    print(f"on_ground={player.on_ground}, air_dodge_ok={player.air_dodge_ok}")

    # Frame 2: Hold shield, press right
    print("\n--- FRAME 2: Hold shield, press right ---")
    pressed2 = {pygame.K_d}  # Only right is freshly pressed
    held2 = {pygame.K_SPACE, pygame.K_d}  # Both shield and right are held
    input_frame2 = InputFrame(pressed=pressed2, held=held2, released=set())

    print(f"Input frame 2: pressed={pressed2}, held={held2}")

    player.update(input_frame2, platforms, attack_group)

    print(
        f"After right press: pos=({player.rect.centerx}, {player.rect.centery}), vel=({player.vel.x}, {player.vel.y})"
    )
    print(f"State: {player.fsm.state}, dodge_timer: {player.dodge_timer}")

    # Check if horizontal velocity was applied
    if abs(player.vel.x) > 0.1:
        print(f"✅ SUCCESS: Horizontal velocity applied: {player.vel.x}")
        return True
    else:
        print(f"❌ FAILED: No horizontal velocity applied, vel.x = {player.vel.x}")
        return False


def test_simultaneous_shield_direction():
    """Test simultaneous shield+direction press for comparison"""
    print("\n=== Simultaneous Shield+Direction Test (for comparison) ===")

    player = create_test_player()
    platforms = []
    attack_group = pygame.sprite.Group()

    print(
        f"Initial state: pos=({player.rect.centerx}, {player.rect.centery}), vel=({player.vel.x}, {player.vel.y})"
    )

    # Frame 1: Press shield and right simultaneously
    print("\n--- FRAME 1: Press shield + right simultaneously ---")
    pressed1 = {pygame.K_SPACE, pygame.K_d}
    held1 = {pygame.K_SPACE, pygame.K_d}
    input_frame1 = InputFrame(pressed=pressed1, held=held1, released=set())

    player.update(input_frame1, platforms, attack_group)

    print(
        f"After simultaneous press: pos=({player.rect.centerx}, {player.rect.centery}), vel=({player.vel.x}, {player.vel.y})"
    )
    print(f"State: {player.fsm.state}, dodge_timer: {player.dodge_timer}")

    if abs(player.vel.x) > 0.1:
        print(f"✅ SUCCESS: Horizontal velocity applied: {player.vel.x}")
        return True
    else:
        print(f"❌ FAILED: No horizontal velocity applied, vel.x = {player.vel.x}")
        return False


def main():
    """Run focused shield-then-direction tests"""
    pygame.init()

    print("Focused Shield-Then-Direction Air Dodge Test")
    print("=" * 60)

    # Test the problematic case
    success1 = test_shield_then_direction_detailed()

    # Test the working case for comparison
    success2 = test_simultaneous_shield_direction()

    print("\n" + "=" * 60)
    print(f"Shield-then-direction: {'PASSED' if success1 else 'FAILED'}")
    print(f"Simultaneous: {'PASSED' if success2 else 'FAILED'}")

    if success1:
        print("🎉 Shield-then-direction air dodge is working!")
    else:
        print("❌ Shield-then-direction air dodge needs debugging")

    return success1


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
