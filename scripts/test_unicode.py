#!/usr/bin/env python3
"""
Simple test to verify Unicode rendering is working.
"""

import pygame
import sys
import os

# Add the pycats module to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "pycats"))


def test_unicode_rendering():
    """Test Unicode character rendering."""
    pygame.init()

    # Create a simple display
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Unicode Test")

    # Import our text renderer
    from pycats.text_utils import text_renderer

    # Test characters
    test_chars = ["►", "◄", "↑", "↓", "✓", "→", "←"]

    print(f"Unicode font name: {text_renderer.unicode_font_name}")

    # Clear screen
    screen.fill((50, 50, 50))

    # Test render_text_mixed
    y = 50
    for char in test_chars:
        text = f"Mixed render: {char} <- should be Unicode"
        text_renderer.render_text_mixed(text, 24, (255, 255, 255), screen, (50, y))
        y += 30

    # Test render_unicode_char
    y += 30
    for i, char in enumerate(test_chars):
        text_renderer.render_unicode_char(
            char, 32, (255, 255, 0), screen, (50 + i * 40, y), center=True
        )

    # Add text
    text_renderer.render_text_simple(
        "Unicode chars above (yellow):", 20, (255, 255, 255), screen, (50, y + 40)
    )

    pygame.display.flip()

    # Wait for a key press
    print(
        "Unicode test window opened. Check if Unicode characters are displayed properly."
    )
    print("Press any key in the window to close, or close the window.")

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                running = False

    pygame.quit()


if __name__ == "__main__":
    test_unicode_rendering()
