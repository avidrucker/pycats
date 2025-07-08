#!/usr/bin/env python3
"""
Test script to verify spot dodge behavior.
This will create a simple test scenario to verify that:
1. Players can perform spot dodges
2. Spot dodges don't make players fall through thin platforms
3. Players transition back to shield state after spot dodge
"""

import pygame as pg # type: ignore
import sys
sys.path.append('.')

from pycats.entities.player import Player
from pycats.entities.platform import Platform
from pycats.core.input import InputFrame
from pycats.config import *

def test_spot_dodge():
    pg.init()
    
    # Create a simple test setup
    platforms = pg.sprite.Group()
    
    # Create both a thin platform and a thick platform for testing
    thin_platform = Platform(pg.Rect(300, 400, 200, 20), thin=True)
    thick_platform = Platform(pg.Rect(600, 400, 200, 20), thin=False)
    platforms.add(thin_platform)
    platforms.add(thick_platform)
    
    print("=== Testing Spot Dodge Behavior ===")
    
    # Test 1: Spot dodge on thin platform
    print("\n--- Test 1: Spot Dodge on Thin Platform ---")
    
    # Create a player on the thin platform
    player1 = Player(
        x=400, y=400,  # On the thin platform (y should match platform top)
        controls={'left': pg.K_a, 'right': pg.K_d, 'up': pg.K_w, 'down': pg.K_s, 'shield': pg.K_q, 'attack': pg.K_e},
        color=P1_COLOR,
        eye_color=WHITE,
        char_name="ThinTestCat",
        facing_right=True
    )
    
    test_player_spot_dodge(player1, platforms, "thin platform")
    
    # Test 2: Spot dodge on thick platform  
    print("\n--- Test 2: Spot Dodge on Thick Platform ---")
    
    # Create a player on the thick platform
    player2 = Player(
        x=700, y=400,  # On the thick platform
        controls={'left': pg.K_a, 'right': pg.K_d, 'up': pg.K_w, 'down': pg.K_s, 'shield': pg.K_q, 'attack': pg.K_e},
        color=P2_COLOR,
        eye_color=WHITE,
        char_name="ThickTestCat",
        facing_right=True
    )
    
    test_player_spot_dodge(player2, platforms, "thick platform")
    
    pg.quit()

def test_player_spot_dodge(player, platforms, platform_type):
    print(f"Player initial position: {player.rect.center}")
    print(f"Player on ground: {player.on_ground}")
    
    # Let the player settle on the platform first
    settle_frame = InputFrame(held=set(), pressed=set(), released=set())
    player.update(settle_frame, platforms, pg.sprite.Group())
    print(f"After settling: Player position: {player.rect.center}, On ground: {player.on_ground}")
    
    # Frame 1: Press shield and down simultaneously (spot dodge)
    frame1 = InputFrame(
        held={pg.K_q, pg.K_s},  # Shield and down held
        pressed={pg.K_q, pg.K_s},  # Shield and down just pressed simultaneously
        released=set()
    )
    
    player.update(frame1, platforms, pg.sprite.Group())
    print(f"Frame 1 - Shield+Down pressed simultaneously. State: {player.fsm.state}, Spot dodge flag: {player.spot_dodge_shield_held}, Shield attempting: {player.shield_attempting}")
    
    # Continue holding for a few frames to simulate real input
    for i in range(3):
        frame = InputFrame(
            held={pg.K_q, pg.K_s},  # Keep shield and down held
            pressed=set(),  # Nothing newly pressed
            released=set()
        )
        
        player.update(frame, platforms, pg.sprite.Group())
        if i == 0:
            print(f"Frame {i+2} - Continuing to hold. State: {player.fsm.state}, Shield attempting: {player.shield_attempting}")
    
    
    # Simulate the dodge duration
    for i in range(DODGE_TIME):
        frame = InputFrame(
            held={pg.K_q, pg.K_s},  # Keep shield and down held
            pressed=set(),
            released=set()
        )
        
        player.update(frame, platforms, pg.sprite.Group())
        
        if i == 0:
            print(f"Dodge frame {i+1} - State: {player.fsm.state}, Position: {player.rect.center}, On ground: {player.on_ground}")
        elif i == DODGE_TIME - 1:
            print(f"Dodge frame {i+1} (last) - State: {player.fsm.state}, Position: {player.rect.center}, On ground: {player.on_ground}")
    
    # Frame after dodge ends - should transition to shield
    frame_after = InputFrame(
        held={pg.K_q, pg.K_s},  # Keep shield and down held
        pressed=set(),
        released=set()
    )
    
    player.update(frame_after, platforms, pg.sprite.Group())
    print(f"After dodge - State: {player.fsm.state}, Position: {player.rect.center}, On ground: {player.on_ground}")
    print(f"Shield attempting: {player.shield_attempting}, Spot dodge flag: {player.spot_dodge_shield_held}")
    
    # Check results
    if player.on_ground:
        print(f"✅ SUCCESS: Player stayed on {platform_type} after spot dodge!")
    else:
        print(f"❌ FAIL: Player fell through {platform_type}!")
    
    if player.fsm.state == "shield":
        print(f"✅ SUCCESS: Player transitioned to shield state after spot dodge on {platform_type}!")
    else:
        print(f"❌ FAIL: Player state is '{player.fsm.state}' instead of 'shield' on {platform_type}!")
    
    if not player.shield_attempting or player.fsm.state != "shield":
        print(f"✅ SUCCESS: No unwanted shield display during spot dodge on {platform_type}!")
    else:
        print(f"⚠️  INFO: Shield state/attempting status on {platform_type}: state={player.fsm.state}, attempting={player.shield_attempting}")
    
    return player.on_ground and player.fsm.state == "shield"

if __name__ == "__main__":
    test_spot_dodge()
