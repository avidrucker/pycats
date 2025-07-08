#!/usr/bin/env python3
"""
Test to verify that side air dodges apply horizontal velocity correctly.

This test specifically checks:
1. Left air dodge applies negative horizontal velocity
2. Right air dodge applies positive horizontal velocity
3. Air dodges preserve Y velocity (don't reset it to 0)
4. Air dodges work from both idle-to-air and shield-to-air entry points
"""

import pygame
import sys
import os

# Add the parent directory to sys.path to import the game modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pycats.entities.player import Player, PState
from pycats.entities.platform import Platform
from pycats.core.input import InputFrame
from pycats.config import DODGE_SPEED, PLAYER_SIZE

def create_test_player():
    """Create a test player in the air"""
    controls = {
        'left': pygame.K_a,
        'right': pygame.K_d, 
        'up': pygame.K_w,
        'down': pygame.K_s,
        'shield': pygame.K_SPACE,
        'attack': pygame.K_j
    }
    
    # Position player in air, away from any platforms
    player = Player(200, 100, controls, (255, 160, 64), (0, 0, 0), "TestCat", facing_right=True)
    player.vel.y = 5.0  # Give some downward velocity to simulate falling
    player.on_ground = False
    player.air_dodge_ok = True
    
    return player

def create_input_frame(shield_pressed=False, left_pressed=False, right_pressed=False, down_pressed=False):
    """Create an InputFrame with specified key states"""
    pressed = set()
    held = set()
    released = set()
    
    if shield_pressed:
        pressed.add(pygame.K_SPACE)
        held.add(pygame.K_SPACE)
    if left_pressed:
        pressed.add(pygame.K_a)
        held.add(pygame.K_a)
    if right_pressed:
        pressed.add(pygame.K_d)
        held.add(pygame.K_d)
    if down_pressed:
        pressed.add(pygame.K_s)
        held.add(pygame.K_s)
    
    return InputFrame(pressed=pressed, held=held, released=released)

def test_left_air_dodge():
    """Test that left air dodge applies negative horizontal velocity"""
    print("\n=== Testing Left Air Dodge ===")
    
    player = create_test_player()
    platforms = []
    attack_group = pygame.sprite.Group()
    
    # Store initial state
    initial_y_vel = player.vel.y
    print(f"Initial state: pos=({player.rect.centerx}, {player.rect.centery}), vel=({player.vel.x}, {player.vel.y})")
    print(f"Initial Y velocity: {initial_y_vel}")
    
    # Press shield + left simultaneously (air dodge left)
    input_frame = create_input_frame(shield_pressed=True, left_pressed=True)
    player.update(input_frame, platforms, attack_group)
    
    print(f"After left air dodge: pos=({player.rect.centerx}, {player.rect.centery}), vel=({player.vel.x}, {player.vel.y})")
    print(f"State: {player.fsm.state}")
    print(f"Dodge timer: {player.dodge_timer}")
    print(f"Air dodge ok: {player.air_dodge_ok}")
    
    # Verify results
    success = True
    
    # Should be in dodge state
    if player.fsm.state != "dodge":
        print(f"❌ Expected state 'dodge', got '{player.fsm.state}'")
        success = False
    
    # Should have negative horizontal velocity (left)
    expected_x_vel = -DODGE_SPEED
    if abs(player.vel.x - expected_x_vel) > 0.1:
        print(f"❌ Expected X velocity {expected_x_vel}, got {player.vel.x}")
        success = False
    
    # Should preserve Y velocity (not reset to 0) - allow small tolerance for gravity
    if abs(player.vel.y - initial_y_vel) > 1.0:  # Allow some tolerance for gravity
        print(f"❌ Expected Y velocity preserved at ~{initial_y_vel}, got {player.vel.y}")
        success = False
    
    # Should not be spot dodge
    if player.spot_dodge_shield_held:
        print(f"❌ Air dodge should not set spot_dodge_shield_held=True")
        success = False
    
    # Should consume air dodge
    if player.air_dodge_ok:
        print(f"❌ Air dodge should set air_dodge_ok=False")
        success = False
    
    if success:
        print("✅ Left air dodge test PASSED")
    else:
        print("❌ Left air dodge test FAILED")
    
    return success

def test_right_air_dodge():
    """Test that right air dodge applies positive horizontal velocity"""
    print("\n=== Testing Right Air Dodge ===")
    
    player = create_test_player()
    platforms = []
    attack_group = pygame.sprite.Group()
    
    # Store initial state
    initial_y_vel = player.vel.y
    print(f"Initial state: pos=({player.rect.centerx}, {player.rect.centery}), vel=({player.vel.x}, {player.vel.y})")
    print(f"Initial Y velocity: {initial_y_vel}")
    
    # Press shield + right simultaneously (air dodge right)
    input_frame = create_input_frame(shield_pressed=True, right_pressed=True)
    player.update(input_frame, platforms, attack_group)
    
    print(f"After right air dodge: pos=({player.rect.centerx}, {player.rect.centery}), vel=({player.vel.x}, {player.vel.y})")
    print(f"State: {player.fsm.state}")
    print(f"Dodge timer: {player.dodge_timer}")
    print(f"Air dodge ok: {player.air_dodge_ok}")
    
    # Verify results
    success = True
    
    # Should be in dodge state
    if player.fsm.state != "dodge":
        print(f"❌ Expected state 'dodge', got '{player.fsm.state}'")
        success = False
    
    # Should have positive horizontal velocity (right)
    expected_x_vel = DODGE_SPEED
    if abs(player.vel.x - expected_x_vel) > 0.1:
        print(f"❌ Expected X velocity {expected_x_vel}, got {player.vel.x}")
        success = False
    
    # Should preserve Y velocity (not reset to 0) - allow small tolerance for gravity
    if abs(player.vel.y - initial_y_vel) > 1.0:  # Allow some tolerance for gravity
        print(f"❌ Expected Y velocity preserved at ~{initial_y_vel}, got {player.vel.y}")
        success = False
    
    # Should not be spot dodge
    if player.spot_dodge_shield_held:
        print(f"❌ Air dodge should not set spot_dodge_shield_held=True")
        success = False
    
    # Should consume air dodge
    if player.air_dodge_ok:
        print(f"❌ Air dodge should set air_dodge_ok=False")
        success = False
    
    if success:
        print("✅ Right air dodge test PASSED")
    else:
        print("❌ Right air dodge test FAILED")
    
    return success

def test_shield_then_direction_air_dodge():
    """Test air dodge initiated by pressing shield first, then direction"""
    print("\n=== Testing Shield-Then-Direction Air Dodge ===")
    
    player = create_test_player()
    platforms = []
    attack_group = pygame.sprite.Group()
    
    # Store initial state
    initial_y_vel = player.vel.y
    print(f"Initial state: pos=({player.rect.centerx}, {player.rect.centery}), vel=({player.vel.x}, {player.vel.y})")
    
    # First frame: press shield only (should start neutral air dodge)
    input_frame = create_input_frame(shield_pressed=True)
    player.update(input_frame, platforms, attack_group)
    
    print(f"After shield press: pos=({player.rect.centerx}, {player.rect.centery}), vel=({player.vel.x}, {player.vel.y})")
    print(f"State: {player.fsm.state}")
    
    # Should be in dodge state with no horizontal velocity (neutral air dodge)
    if player.fsm.state != "dodge":
        print(f"❌ Expected state 'dodge' after shield press, got '{player.fsm.state}'")
        return False
    
    if abs(player.vel.x) > 0.1:
        print(f"❌ Expected neutral air dodge (X vel = 0), got X vel = {player.vel.x}")
        return False
    
    # Second frame: hold shield and press right (should modify to directional dodge)
    input_frame = create_input_frame(shield_pressed=False, right_pressed=True)
    input_frame.held.add(pygame.K_SPACE)  # Shield is held from previous frame
    player.update(input_frame, platforms, attack_group)
    
    print(f"After right press: pos=({player.rect.centerx}, {player.rect.centery}), vel=({player.vel.x}, {player.vel.y})")
    print(f"State: {player.fsm.state}")
    
    # Check if horizontal velocity was applied
    success = True
    if abs(player.vel.x) < 0.1:
        print(f"❌ Expected horizontal velocity after direction press, got X vel = {player.vel.x}")
        success = False
    else:
        print(f"✅ Horizontal velocity applied: {player.vel.x}")
    
    if success:
        print("✅ Shield-then-direction air dodge test PASSED")
    else:
        print("❌ Shield-then-direction air dodge test FAILED")
    
    return success

def test_air_dodge_vs_ground_dodge():
    """Test that air dodges and ground dodges behave differently"""
    print("\n=== Testing Air vs Ground Dodge Behavior ===")
    
    success = True
    
    # Test air dodge
    print("\nTesting air dodge:")
    air_player = create_test_player()
    air_player.vel.y = 3.0  # Falling
    air_platforms = []
    air_attack_group = pygame.sprite.Group()
    
    air_input = create_input_frame(shield_pressed=True, right_pressed=True)
    air_player.update(air_input, air_platforms, air_attack_group)
    
    print(f"Air dodge result: vel=({air_player.vel.x}, {air_player.vel.y}), spot_dodge={air_player.spot_dodge_shield_held}")
    
    # Test ground dodge
    print("\nTesting ground dodge:")
    ground_player = create_test_player()
    ground_player.rect.midbottom = (200, 300)  # On ground
    ground_player.vel.y = 0
    ground_player.on_ground = True
    
    # Create a platform for the ground player
    platform_rect = pygame.Rect(100, 300, 200, 20)
    platform = Platform(platform_rect, thin=False)
    ground_platforms = [platform]
    ground_attack_group = pygame.sprite.Group()
    
    ground_input = create_input_frame(shield_pressed=True, right_pressed=True)
    ground_player.update(ground_input, ground_platforms, ground_attack_group)
    
    print(f"Ground dodge result: vel=({ground_player.vel.x}, {ground_player.vel.y}), spot_dodge={ground_player.spot_dodge_shield_held}")
    
    # Verify differences
    # Air dodge should preserve Y velocity, ground dodge should reset Y to 0 - allow tolerance for gravity
    if abs(air_player.vel.y - 3.0) > 1.0:  # Allow tolerance for gravity
        print(f"❌ Air dodge should preserve Y velocity, expected ~3.0, got {air_player.vel.y}")
        success = False
    
    if abs(ground_player.vel.y) > 0.1:
        print(f"❌ Ground dodge should reset Y velocity to 0, got {ground_player.vel.y}")
        success = False
    
    # Both should have same horizontal velocity magnitude
    if abs(abs(air_player.vel.x) - abs(ground_player.vel.x)) > 0.1:
        print(f"❌ Air and ground dodge should have same horizontal speed, air={abs(air_player.vel.x)}, ground={abs(ground_player.vel.x)}")
        success = False
    
    # Neither should be spot dodge for directional dodges
    if air_player.spot_dodge_shield_held or ground_player.spot_dodge_shield_held:
        print(f"❌ Directional dodges should not set spot_dodge_shield_held")
        success = False
    
    if success:
        print("✅ Air vs ground dodge behavior test PASSED")
    else:
        print("❌ Air vs ground dodge behavior test FAILED")
    
    return success

def main():
    """Run all side air dodge velocity tests"""
    pygame.init()
    
    print("Testing Side Air Dodge Velocity")
    print("=" * 50)
    
    tests = [
        test_left_air_dodge,
        test_right_air_dodge,
        test_shield_then_direction_air_dodge,
        test_air_dodge_vs_ground_dodge,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All side air dodge velocity tests PASSED!")
        return True
    else:
        print("❌ Some tests FAILED!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
