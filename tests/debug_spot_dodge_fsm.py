#!/usr/bin/env python3
"""Debug script to examine FSM behavior during spot dodge."""

try:
    import pygame
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

    from pycats.entities.player import Player
    from pycats.entities.platform import Platform
    from pycats.core.input import InputFrame
    from pycats.config import DODGE_TIME

    print("Imports successful")
    
    pygame.init()
    print("Pygame initialized")
    
    # Create test environment
    platforms = [
        Platform(pygame.Rect(300, 400, 200, 30), True),  # Thin platform
    ]
    print("Platform created")
    
    controls = {'left': pygame.K_a, 'right': pygame.K_d, 'up': pygame.K_w, 'down': pygame.K_s, 'shield': pygame.K_q, 'attack': pygame.K_e}
    player = Player(400, 370, controls, (255, 255, 255), (0, 0, 0), "TestPlayer")
    print("Player created")
    
    print("=== Debug Spot Dodge FSM Transitions ===")
    print(f"DODGE_TIME constant: {DODGE_TIME}")
    print(f"Initial state: {player.fsm.state}")
    print(f"Initial on_ground: {player.on_ground}")
    print(f"Initial position: {player.rect.center}")
    
    pygame.quit()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
