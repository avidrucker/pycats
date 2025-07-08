#!/usr/bin/env python3
"""Test to specifically check if air dodges are getting zero velocity in certain scenarios."""

import pygame as pg
import sys
sys.path.append('.')

from pycats.entities.player import Player
from pycats.entities.platform import Platform
from pycats.core.input import InputFrame
from pycats.config import DODGE_SPEED

def test_air_dodge_zero_velocity_issue():
    pg.init()
    
    platforms = [Platform(pg.Rect(200, 500, 400, 30), False)]
    
    print("=== Testing Air Dodge Zero Velocity Issue ===")
    
    # Test different scenarios that might cause zero velocity
    scenarios = [
        {
            "name": "From idle->jump->air dodge",
            "setup": lambda player: [
                # Start on ground
                InputFrame(held=set(), pressed=set(), released=set()),
                # Jump
                InputFrame(held={pg.K_w}, pressed={pg.K_w}, released=set()),
                # In air, no input for a frame
                InputFrame(held=set(), pressed=set(), released=set()),
            ],
            "air_dodge": InputFrame(held={pg.K_q, pg.K_d}, pressed={pg.K_q, pg.K_d}, released=set())
        },
        {
            "name": "From fall->air dodge",
            "setup": lambda player: [
                # Let fall for a few frames
                InputFrame(held=set(), pressed=set(), released=set()),
                InputFrame(held=set(), pressed=set(), released=set()),
                InputFrame(held=set(), pressed=set(), released=set()),
            ],
            "air_dodge": InputFrame(held={pg.K_q, pg.K_d}, pressed={pg.K_q, pg.K_d}, released=set())
        },
        {
            "name": "Shield first, then direction (while in air)",
            "setup": lambda player: [
                # Let fall for a few frames
                InputFrame(held=set(), pressed=set(), released=set()),
                InputFrame(held=set(), pressed=set(), released=set()),
                # Press shield first
                InputFrame(held={pg.K_q}, pressed={pg.K_q}, released=set()),
            ],
            "air_dodge": InputFrame(held={pg.K_q, pg.K_d}, pressed={pg.K_d}, released=set())
        }
    ]
    
    for scenario in scenarios:
        print(f"\n--- {scenario['name']} ---")
        
        controls = {'left': pg.K_a, 'right': pg.K_d, 'up': pg.K_w, 'down': pg.K_s, 'shield': pg.K_q, 'attack': pg.K_e}
        player = Player(400, 450, controls, (255, 160, 64), (255, 255, 255), "TestCat")
        
        # Run setup frames
        for frame in scenario["setup"](player):
            player.update(frame, platforms, pg.sprite.Group())
        
        print(f"After setup: pos={player.rect.center}, on_ground={player.on_ground}, state={player.fsm.state}, vel={player.vel}")
        
        # Trigger air dodge
        start_pos = player.rect.centerx
        player.update(scenario["air_dodge"], platforms, pg.sprite.Group())
        
        print(f"After air dodge: state={player.fsm.state}, vel={player.vel}")
        
        # Check if velocity is correct
        expected_vel_x = 22  # Right dodge
        if abs(player.vel.x - expected_vel_x) < 0.1:
            print(f"✅ Velocity correct: {player.vel.x}")
        else:
            print(f"❌ Velocity incorrect: got {player.vel.x}, expected {expected_vel_x}")
        
        # Test one frame of movement
        continue_frame = InputFrame(held={pg.K_q, pg.K_d}, pressed=set(), released=set())
        player.update(continue_frame, platforms, pg.sprite.Group())
        
        end_pos = player.rect.centerx
        distance = end_pos - start_pos
        print(f"Distance moved in 1 frame: {distance}px")
        
        if abs(distance) < 5:
            print(f"❌ Almost no movement detected - velocity might be getting zeroed")
        else:
            print(f"✅ Good movement detected")
    
    pg.quit()

if __name__ == "__main__":
    test_air_dodge_zero_velocity_issue()
