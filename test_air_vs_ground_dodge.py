#!/usr/bin/env python3
"""
Test script to verify air dodge vs ground spot dodge behavior.
This ensures that:
1. Ground spot dodges use special physics (no gravity, no movement)
2. Air dodges use normal physics (gravity, normal movement)
3. No regression in air dodge functionality
"""

import pygame as pg
import sys
sys.path.append('.')

from pycats.entities.player import Player
from pycats.entities.platform import Platform
from pycats.core.input import InputFrame
from pycats.config import *

def test_air_vs_ground_dodge():
    pg.init()
    
    # Create platforms
    platforms = pg.sprite.Group()
    platform = Platform(pg.Rect(300, 400, 200, 20), thin=True)
    platforms.add(platform)
    
    print("=== Testing Air Dodge vs Ground Spot Dodge ===")
    
    # Test 1: Ground spot dodge (should use special physics)
    print("\n--- Test 1: Ground Spot Dodge ---")
    player1 = Player(
        x=400, y=400,
        controls={'left': pg.K_a, 'right': pg.K_d, 'up': pg.K_w, 'down': pg.K_s, 'shield': pg.K_q, 'attack': pg.K_e},
        color=P1_COLOR,
        eye_color=WHITE,
        char_name="GroundCat",
        facing_right=True
    )
    
    # Settle on platform
    settle_frame = InputFrame(held=set(), pressed=set(), released=set())
    player1.update(settle_frame, platforms, pg.sprite.Group())
    print(f"Ground test - Initial: pos={player1.rect.center}, on_ground={player1.on_ground}")
    
    # Trigger ground spot dodge
    ground_spot_dodge_frame = InputFrame(
        held={pg.K_q, pg.K_s},  # Shield and down held
        pressed={pg.K_q, pg.K_s},  # Both just pressed
        released=set()
    )
    player1.update(ground_spot_dodge_frame, platforms, pg.sprite.Group())
    print(f"Ground spot dodge - After trigger: state={player1.fsm.state}, spot_dodge_flag={player1.spot_dodge_shield_held}")
    
    # Simulate a few frames
    for i in range(5):
        frame = InputFrame(held={pg.K_q, pg.K_s}, pressed=set(), released=set())
        player1.update(frame, platforms, pg.sprite.Group())
        if i == 0:
            print(f"Ground spot dodge - Frame {i+1}: pos={player1.rect.center}, vel={player1.vel}, on_ground={player1.on_ground}")
    
    # Test 2: Air dodge (should use normal physics)
    print("\n--- Test 2: Air Dodge ---")
    player2 = Player(
        x=400, y=300,  # Start in air
        controls={'left': pg.K_a, 'right': pg.K_d, 'up': pg.K_w, 'down': pg.K_s, 'shield': pg.K_q, 'attack': pg.K_e},
        color=P2_COLOR,
        eye_color=WHITE,
        char_name="AirCat",
        facing_right=True
    )
    
    # Let player fall a bit first
    fall_frame = InputFrame(held=set(), pressed=set(), released=set())
    player2.update(fall_frame, platforms, pg.sprite.Group())
    print(f"Air test - Initial: pos={player2.rect.center}, on_ground={player2.on_ground}, vel={player2.vel}")
    
    # Trigger air dodge (shield only, no direction)
    air_dodge_frame = InputFrame(
        held={pg.K_q},  # Shield held
        pressed={pg.K_q},  # Shield just pressed
        released=set()
    )
    player2.update(air_dodge_frame, platforms, pg.sprite.Group())
    print(f"Air dodge - After trigger: state={player2.fsm.state}, spot_dodge_flag={player2.spot_dodge_shield_held}")
    
    # Simulate a few frames
    for i in range(5):
        frame = InputFrame(held={pg.K_q}, pressed=set(), released=set())
        player2.update(frame, platforms, pg.sprite.Group())
        if i == 0:
            print(f"Air dodge - Frame {i+1}: pos={player2.rect.center}, vel={player2.vel}, on_ground={player2.on_ground}")
        elif i == 4:
            print(f"Air dodge - Frame {i+1}: pos={player2.rect.center}, vel={player2.vel}, on_ground={player2.on_ground}")
    
    # Results
    print("\n--- Results ---")
    if player1.spot_dodge_shield_held or (player1.fsm.state == "dodge" and abs(player1.vel.y) < 0.1):
        print("✅ Ground spot dodge: Using special physics (no gravity)")
    else:
        print("❌ Ground spot dodge: NOT using special physics")
    
    if not player2.spot_dodge_shield_held and player2.vel.y > 0:
        print("✅ Air dodge: Using normal physics (has gravity)")
    else:
        print("❌ Air dodge: Using special physics (should not)")
        print(f"   Debug: spot_dodge_flag={player2.spot_dodge_shield_held}, vel.y={player2.vel.y}")
    
    pg.quit()

if __name__ == "__main__":
    test_air_vs_ground_dodge()
