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
    
    # Create a thin platform
    thin_platform = Platform(pg.Rect(300, 400, 200, 20), thin=True)
    platforms.add(thin_platform)
    
    # Create a player on the thin platform
    player = Player(
        x=400, y=400,  # On the thin platform (y should match platform top)
        controls={'left': pg.K_a, 'right': pg.K_d, 'up': pg.K_w, 'down': pg.K_s, 'shield': pg.K_q, 'attack': pg.K_e},
        color=P1_COLOR,
        eye_color=WHITE,
        char_name="TestCat",
        facing_right=True
    )
    
    # Simulate input frames for spot dodge
    print("=== Testing Spot Dodge Behavior ===")
    print(f"Player initial position: {player.rect.center}")
    print(f"Player on ground: {player.on_ground}")
    print(f"Platform position: {thin_platform.rect}")
    
    # Let the player settle on the platform first
    settle_frame = InputFrame(held=set(), pressed=set(), released=set())
    player.update(settle_frame, platforms, pg.sprite.Group())
    print(f"After settling: Player position: {player.rect.center}, On ground: {player.on_ground}")
    
    # Frame 1: Press shield
    frame1 = InputFrame(
        held={pg.K_q},  # Shield held
        pressed={pg.K_q},  # Shield just pressed
        released=set()
    )
    
    player.update(frame1, platforms, pg.sprite.Group())
    print(f"Frame 1 - Shield pressed. State: {player.fsm.state}, Shield attempting: {player.shield_attempting}")
    
    # Frame 2-3: Continue holding shield, then press down (spot dodge)
    for i in range(2):
        frame = InputFrame(
            held={pg.K_q},  # Shield held
            pressed=set(),  # Nothing newly pressed
            released=set()
        )
        
        player.update(frame, platforms, pg.sprite.Group())
        print(f"Frame {i+2} - Shield held. State: {player.fsm.state}")
    
    # Frame 4: Press down while holding shield (trigger spot dodge)
    frame4 = InputFrame(
        held={pg.K_q, pg.K_s},  # Shield and down held
        pressed={pg.K_s},  # Down just pressed
        released=set()
    )
    
    player.update(frame4, platforms, pg.sprite.Group())
    print(f"Frame 4 - Down pressed with shield. State: {player.fsm.state}, Spot dodge flag: {player.spot_dodge_shield_held}")
    
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
    
    # Check if player stayed on platform
    if player.on_ground and player.rect.bottom <= thin_platform.rect.top + 2:
        print("✅ SUCCESS: Player stayed on thin platform after spot dodge!")
    else:
        print("❌ FAIL: Player fell through thin platform!")
    
    if player.fsm.state == "shield":
        print("✅ SUCCESS: Player transitioned to shield state after spot dodge!")
    else:
        print(f"❌ FAIL: Player state is '{player.fsm.state}' instead of 'shield'!")
    
    pg.quit()

if __name__ == "__main__":
    test_spot_dodge()
