#!/usr/bin/env python3
import pygame
pygame.init()

import sys
import os
sys.path.insert(0, 'pycats')

print("=== Testing Unicode Rendering ===")

from pycats.text_utils import text_renderer, quick_unicode_test

# Run diagnostic
quick_unicode_test()

# Test the actual rendering functions
print("\n=== Testing render_text_mixed ===")
test_surface = pygame.Surface((100, 30))
test_chars = ["►", "◄", "↑", "↓"]

for char in test_chars:
    test_text = f"Arrow: {char}"
    try:
        rect = text_renderer.render_text_mixed(test_text, 16, (255, 255, 255), test_surface, (0, 0))
        print(f"✓ Mixed render of '{test_text}' succeeded, rect: {rect}")
    except Exception as e:
        print(f"✗ Mixed render of '{test_text}' failed: {e}")

print("\n=== Testing render_unicode_char ===")
for char in test_chars:
    try:
        rect = text_renderer.render_unicode_char(char, 16, (255, 255, 255), test_surface, (0, 0))
        print(f"✓ Unicode char render of '{char}' succeeded, rect: {rect}")
    except Exception as e:
        print(f"✗ Unicode char render of '{char}' failed: {e}")

print("\n=== Testing tofu detection ===")
font = pygame.font.Font(None, 16)
for char in test_chars:
    char_surface = font.render(char, True, (255, 255, 255))
    is_tofu = text_renderer._is_tofu(char, char_surface, font)
    print(f"Character '{char}': width={char_surface.get_width()}, is_tofu={is_tofu} {'✗ Wrong!' if is_tofu else '✓ Good'}")

print("=== Test Complete ===")
