#!/usr/bin/env python3

"""
Quick test to verify character selection screen works.
"""

import pygame
import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pycats.config import CAT_CHARACTERS, CHAR_SELECT_BG_COLOR
from tests.char_select import CharacterSelector

def test_character_selector():
    print("Starting pygame...")
    pygame.init()
    
    print("Setting up controls...")
    # Test controls
    P1_KEYS = {
        'left': pygame.K_a,
        'right': pygame.K_d,
        'up': pygame.K_w,
        'down': pygame.K_s,
        'attack': pygame.K_v,
    }
    
    P2_KEYS = {
        'left': pygame.K_LEFT,
        'right': pygame.K_RIGHT,
        'up': pygame.K_UP,
        'down': pygame.K_DOWN,
        'attack': pygame.K_SLASH,
    }
    
    print("Creating character selector...")
    # Create character selector
    selector = CharacterSelector(P1_KEYS, P2_KEYS)
    
    print("Character selector created successfully")
    print(f"Available characters: {selector.characters}")
    print(f"P1 cursor: {selector.p1_cursor}")
    print(f"P2 cursor: {selector.p2_cursor}")
    print(f"Character data: {list(CAT_CHARACTERS.keys())}")
    
    # Test that both ready works
    assert not selector.both_ready(), "Both ready should be False initially"
    
    # Simulate picking characters
    selector.p1_token = "ghost"
    selector.p2_token = "void"
    
    assert selector.both_ready(), "Both ready should be True after selection"
    
    p1_char, p2_char = selector.get_selected_characters()
    print(f"Selected characters: P1={p1_char}, P2={p2_char}")
    
    pygame.quit()
    print("Test passed!")

if __name__ == "__main__":
    test_character_selector()
