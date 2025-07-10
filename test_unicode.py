#!/usr/bin/env python3
"""
Test script to check Unicode support in pygame fonts
"""
import pygame

pygame.init()

# Check available fonts
available_fonts = pygame.font.get_fonts()
print("Available fonts:")
for font in sorted(available_fonts):
    print(f"  {font}")

print("\nTesting Unicode support:")

# Test various fonts with Unicode characters
test_chars = ["✓", "✗", "→", "←", "↑", "↓", "★", "♥", "♦", "♣", "♠"]

for font_name in [None, 'arial', 'dejavusans', 'liberation', 'noto']:
    try:
        if font_name:
            font = pygame.font.SysFont(font_name, 24)
            print(f"\nFont: {font_name}")
        else:
            font = pygame.font.SysFont(None, 24)
            print(f"\nFont: default")
        
        for char in test_chars:
            try:
                surface = font.render(char, True, (255, 255, 255))
                print(f"  {char} - OK")
            except Exception as e:
                print(f"  {char} - Failed: {e}")
    except Exception as e:
        print(f"Font {font_name} failed to load: {e}")

pygame.quit()
