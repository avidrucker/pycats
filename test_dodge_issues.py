#!/usr/bin/env python3
"""
Test script to identify specific dodge issues:
1. Air dodge (shield only) zeroing velocity when it shouldn't
2. Side dodge rolling at half speed/distance
3. Visual state issues with simultaneous shield+direction presses
"""

import pygame as pg
import sys
sys.path.append('.')

from pycats.entities.player import Player
from pycats.entities.platform import Platform
from pycats.core.input import InputFrame
from pycats.config import *

def test_dodge_issues():
    pg.init()
    
    # Create platforms
    platforms = pg.sprite.Group()
    platform = Platform(pg.Rect(300, 400, 200, 20), thin=False)
    platforms.add(platform)
    
    print("=== Testing Dodge Issues ===")
    
    # Test 1: Air dodge velocity issue
    print("\n--- Test 1: Air Dodge Velocity Issue ---")
    player1 = Player(
        x=400, y=300,  # Start in air
        controls={'left': pg.K_a, 'right': pg.K_d, 'up': pg.K_w, 'down': pg.K_s, 'shield': pg.K_q, 'attack': pg.K_e},
        color=P1_COLOR,
        eye_color=WHITE,
        char_name="AirCat"
    )
    
    # Let player fall to get some velocity
    for i in range(3):
        fall_frame = InputFrame(held=set(), pressed=set(), released=set())
        player1.update(fall_frame, platforms, pg.sprite.Group())
    
    print(f"Before air dodge: pos={player1.rect.center}, vel={player1.vel}, on_ground={player1.on_ground}")
    
    # Trigger air dodge (shield only, no direction)
    air_dodge_frame = InputFrame(
        held={pg.K_q},  # Shield held
        pressed={pg.K_q},  # Shield just pressed
        released=set()
    )
    player1.update(air_dodge_frame, platforms, pg.sprite.Group())
    print(f"After air dodge trigger: state={player1.fsm.state}, vel={player1.vel}, spot_dodge_flag={player1.spot_dodge_shield_held}")
    
    # Continue for a few frames
    for i in range(3):
        frame = InputFrame(held={pg.K_q}, pressed=set(), released=set())
        player1.update(frame, platforms, pg.sprite.Group())
        print(f"Air dodge frame {i+1}: vel={player1.vel}, pos={player1.rect.center}")
    
    # Test 2: Side dodge speed issue
    print("\n--- Test 2: Side Dodge Speed/Distance ---")
    player2 = Player(
        x=400, y=400,
        controls={'left': pg.K_a, 'right': pg.K_d, 'up': pg.K_w, 'down': pg.K_s, 'shield': pg.K_q, 'attack': pg.K_e},
        color=P2_COLOR,
        eye_color=WHITE,
        char_name="GroundCat"
    )
    
    # Settle on ground
    settle_frame = InputFrame(held=set(), pressed=set(), released=set())
    player2.update(settle_frame, platforms, pg.sprite.Group())
    start_pos = player2.rect.center
    print(f"Before side dodge: pos={start_pos}, on_ground={player2.on_ground}")
    
    # Trigger side dodge (shield + right)
    side_dodge_frame = InputFrame(
        held={pg.K_q, pg.K_d},  # Shield and right held
        pressed={pg.K_q, pg.K_d},  # Both just pressed
        released=set()
    )
    player2.update(side_dodge_frame, platforms, pg.sprite.Group())
    print(f"After side dodge trigger: state={player2.fsm.state}, vel={player2.vel}, spot_dodge_flag={player2.spot_dodge_shield_held}")
    print(f"Image color after trigger: {player2.image.get_at((0,0))}")  # Check if stuck white
    
    # Continue dodge for full duration
    total_distance = 0
    for i in range(DODGE_TIME):
        frame = InputFrame(held={pg.K_q, pg.K_d}, pressed=set(), released=set())
        old_pos = player2.rect.center
        player2.update(frame, platforms, pg.sprite.Group())
        new_pos = player2.rect.center
        frame_distance = abs(new_pos[0] - old_pos[0])
        total_distance += frame_distance
        
        if i == 0:
            print(f"Side dodge frame 1: vel={player2.vel}, moved={frame_distance}px")
        elif i == DODGE_TIME - 1:
            print(f"Side dodge final frame: vel={player2.vel}, total_distance={total_distance}px")
            print(f"Final image color: {player2.image.get_at((0,0))}")  # Should be normal color
    
    expected_distance = DODGE_SPEED * DODGE_TIME
    print(f"Expected total distance: {expected_distance}px, Actual: {total_distance}px")
    
    # Test 3: Shield state to side dodge transition
    print("\n--- Test 3: Shield -> Side Dodge Transition ---")
    player3 = Player(
        x=400, y=400,
        controls={'left': pg.K_a, 'right': pg.K_d, 'up': pg.K_w, 'down': pg.K_s, 'shield': pg.K_q, 'attack': pg.K_e},
        color=(128, 128, 255),
        eye_color=WHITE,
        char_name="ShieldCat"
    )
    
    # Settle on ground
    settle_frame = InputFrame(held=set(), pressed=set(), released=set())
    player3.update(settle_frame, platforms, pg.sprite.Group())
    
    # Enter shield state first
    shield_frame = InputFrame(held={pg.K_q}, pressed={pg.K_q}, released=set())
    player3.update(shield_frame, platforms, pg.sprite.Group())
    print(f"In shield state: {player3.fsm.state}")
    
    # Now add direction to trigger dodge from shield state
    shield_right_frame = InputFrame(
        held={pg.K_q, pg.K_d},  # Shield and right held
        pressed={pg.K_d},  # Right just pressed (shield already held)
        released=set()
    )
    player3.update(shield_right_frame, platforms, pg.sprite.Group())
    print(f"Shield->Dodge transition: state={player3.fsm.state}, vel={player3.vel}")
    print(f"Image color: {player3.image.get_at((0,0))}")
    
    pg.quit()

if __name__ == "__main__":
    test_dodge_issues()
