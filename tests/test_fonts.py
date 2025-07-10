#!/usr/bin/env python3
"""
Font diagnostic test script for the cat fighting game.
Run this to see which fonts support Unicode arrows and symbols.
"""

import pygame
import sys
import os

# Add the pycats module to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pycats'))

from pycats.text_utils import run_font_diagnostics

def main():
    """Run font diagnostics."""
    print("Initializing pygame...")
    pygame.init()
    pygame.font.init()
    
    print("Running font capability diagnostics...\n")
    run_font_diagnostics()
    
    pygame.quit()
    print("Diagnostics complete!")

if __name__ == "__main__":
    main()
