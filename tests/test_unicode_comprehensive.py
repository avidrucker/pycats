#!/usr/bin/env python3
"""
Comprehensive test for Unicode font detection and rendering.

This test verifies:
1. Font detection finds the best Unicode font
2. Character whitelisting works correctly  
3. Unicode characters render without tofu
4. Emoji support works if available
5. ASCII fallbacks work for unsupported characters
"""

import pygame
import sys
import os

# Add the pycats module to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pycats'))

def test_unicode_system():
    """Test the complete Unicode rendering system."""
    print("=== Comprehensive Unicode Test ===")
    
    pygame.init()
    
    from pycats.text_utils import TextRenderer
    
    # Create a fresh text renderer to see the detection process
    print("\n--- Font Detection ---")
    text_renderer = TextRenderer()
    
    print(f"\nDetected Unicode font: {text_renderer.unicode_font_name}")
    
    # Test character sets
    test_sets = {
        "Basic Arrows": ["►", "◄", "↑", "↓", "→", "←"],
        "Symbols": ["✓", "✗", "☑", "☐"],
        "Cat Emoji": ["🐱", "🐈", "😸"],
        "Misc Unicode": ["♠", "♣", "♥", "♦", "★", "☆"]
    }
    
    print("\n--- Character Support Test ---")
    
    # Test what characters are supported
    if isinstance(text_renderer.unicode_font_name, dict):
        supported_chars = text_renderer.unicode_font_name["supported_chars"]
        font_name = text_renderer.unicode_font_name["name"]
        print(f"Font: {font_name}")
        print(f"Supported characters: {sorted(list(supported_chars))}")
        
        for category, chars in test_sets.items():
            supported = [char for char in chars if char in supported_chars]
            unsupported = [char for char in chars if char not in supported_chars]
            print(f"\n{category}:")
            if supported:
                print(f"  Supported: {supported}")
            if unsupported:
                print(f"  Unsupported: {unsupported}")
    else:
        print(f"Legacy format detected: {text_renderer.unicode_font_name}")
    
    print("\n--- Rendering Test ---")
    
    # Create a test surface
    test_surface = pygame.Surface((400, 300))
    test_surface.fill((50, 50, 50))
    
    # Test different rendering methods
    y_pos = 20
    
    # Test render_text_mixed
    test_texts = [
        "Arrows: ►◄↑↓ work?",
        "Cats: 🐱🐈😸 visible?",
        "Mixed: Arrow→Cat🐱"
    ]
    
    for text in test_texts:
        try:
            rect = text_renderer.render_text_mixed(
                text, 16, (255, 255, 255), test_surface, (10, y_pos)
            )
            print(f"✓ Mixed render: '{text}' -> rect {rect}")
            y_pos += 25
        except Exception as e:
            print(f"✗ Mixed render failed: '{text}' -> {e}")
    
    y_pos += 10
    
    # Test render_unicode_char
    test_chars = ["►", "🐱", "✓", "★"]
    x_pos = 10
    
    for char in test_chars:
        try:
            rect = text_renderer.render_unicode_char(
                char, 20, (255, 255, 0), test_surface, (x_pos, y_pos)
            )
            print(f"✓ Unicode char: '{char}' -> rect {rect}")
            x_pos += 30
        except Exception as e:
            print(f"✗ Unicode char failed: '{char}' -> {e}")
    
    print("\n--- Visual Test ---")
    print("Opening test window for visual verification...")
    
    # Create display window for visual test
    screen = pygame.display.set_mode((500, 400))
    pygame.display.set_caption("Unicode Test - Check character rendering")
    
    # Render test content
    screen.fill((30, 30, 30))
    
    # Title
    text_renderer.render_text_mixed("Unicode Support Test", 24, (255, 255, 255), screen, (250, 30), center=True)
    
    # Character tests
    y = 70
    for category, chars in test_sets.items():
        text_renderer.render_text_mixed(f"{category}:", 16, (200, 200, 200), screen, (20, y))
        y += 25
        
        x = 40
        for char in chars:
            # Render each character
            rect = text_renderer.render_unicode_char(char, 18, (255, 255, 100), screen, (x, y))
            x += rect.width + 5
            
            # Add fallback next to it
            fallback = text_renderer._get_ascii_fallback(char)
            text_renderer.render_text_mixed(f"({fallback})", 12, (150, 150, 150), screen, (x, y + 2))
            x += 30
        
        y += 35
    
    # Instructions
    text_renderer.render_text_mixed("Yellow characters should show Unicode if supported", 14, (200, 200, 200), screen, (20, y + 20))
    text_renderer.render_text_mixed("Gray text shows ASCII fallbacks in parentheses", 14, (200, 200, 200), screen, (20, y + 40))
    text_renderer.render_text_mixed("Press any key to close", 14, (100, 255, 100), screen, (20, y + 70))
    
    pygame.display.flip()
    
    # Wait for input
    print("Visual test window opened. Press any key in the window to close.")
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                running = False
    
    pygame.quit()
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_unicode_system()
