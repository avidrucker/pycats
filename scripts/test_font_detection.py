#!/usr/bin/env python3
"""
Test the new whitelist-based Unicode font detection.
"""

import os
import sys

import pygame

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "pycats"))


def test_font_detection():
    """Test the font detection and character whitelisting."""
    pygame.init()

    from pycats.text_utils import TextRenderer

    # Create a new renderer to test detection
    print("Testing new font detection system...")
    renderer = TextRenderer()

    print(f"Result: {renderer.unicode_font_name}")

    if isinstance(renderer.unicode_font_name, dict):
        print("✓ New whitelist format detected")
        font_info = renderer.unicode_font_name
        print(f"Font name: {font_info['name']}")
        print(f"Supported characters: {sorted(list(font_info['supported_chars']))}")

        # Test a few characters
        test_chars = ["►", "◄", "🐱", "✓"]
        for char in test_chars:
            supported = char in font_info["supported_chars"]
            print(f"  '{char}': {'✓ supported' if supported else '✗ not supported'}")
    else:
        print(f"Legacy format or no Unicode support: {renderer.unicode_font_name}")

    pygame.quit()


if __name__ == "__main__":
    test_font_detection()
