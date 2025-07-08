#!/usr/bin/env python3
"""Test to debug exact dodge velocity issues."""

import pygame as pg
import sys
sys.path.append('.')

from pycats.entities.player import Player
from pycats.entities.platform import Platform
from pycats.core.input import InputFrame
from pycats.config import *

def test_dodge_velocity():
    pg.init()
    
    # Create larger platform to avoid edge issues
    platforms = pg.sprite.Group()
    platform = Platform(pg.Rect(100, 400, 600, 20), thin=False)  # Much larger platform
    platforms.add(platform)
    
    print(f"DODGE_SPEED constant: {DODGE_SPEED}")
    
    player = Player(
        x=400, y=400,  # Center of large platform
        controls={'left': pg.K_a, 'right': pg.K_d, 'up': pg.K_w, 'down': pg.K_s, 'shield': pg.K_q, 'attack': pg.K_e},
        color=P1_COLOR,
        eye_color=WHITE,
        char_name="TestCat"
    )
    
    # Settle on ground
    settle_frame = InputFrame(held=set(), pressed=set(), released=set())
    player.update(settle_frame, platforms, pg.sprite.Group())
    print(f"Settled: pos={player.rect.center}, on_ground={player.on_ground}")
    
    # Trigger side dodge (shield + right)
    print("\n--- Triggering dodge ---")
    side_dodge_frame = InputFrame(
        held={pg.K_q, pg.K_d},
        pressed={pg.K_q, pg.K_d},
        released=set()
    )
    
    print(f"Before dodge: vel={player.vel}, state={player.fsm.state}")
    player.update(side_dodge_frame, platforms, pg.sprite.Group())
    print(f"After dodge: vel={player.vel}, state={player.fsm.state}, dodge_timer={player.dodge_timer}")
    
    # Check for edge blocking
    if hasattr(player, 'dodge_blocked_by_edge'):
        print(f"Edge blocked: {player.dodge_blocked_by_edge}")
    
    # Continue for a few frames to see what happens
    for i in range(5):
        frame = InputFrame(held={pg.K_q, pg.K_d}, pressed=set(), released=set())
        old_pos = player.rect.center[0]
        player.update(frame, platforms, pg.sprite.Group())
        new_pos = player.rect.center[0]
        distance = new_pos - old_pos
        print(f"Frame {i+1}: vel={player.vel}, moved={distance}px, pos={player.rect.center}")
        
        if hasattr(player, 'dodge_blocked_by_edge') and player.dodge_blocked_by_edge:
            print(f"  ^ Edge blocking is active")
    
    pg.quit()

if __name__ == "__main__":
    test_dodge_velocity()
