"""
Text rendering utilities with Unicode support for the cat fighting game.

This module provides:
- Mixed font rendering for Unicode and ASCII characters
- Fallback handling for missing Unicode fonts
- Consistent text rendering across different screens
"""

import pygame


class TextRenderer:
    """Utility class for rendering text with mixed font support."""

    def __init__(self, run_diagnostics=False):
        # Ensure pygame font system is initialized
        if not pygame.font.get_init():
            pygame.font.init()

        # Cache fonts to avoid recreating them
        self.font_cache = {}

        # Run diagnostic test if requested
        if run_diagnostics:
            self.test_font_capabilities()

        self.unicode_font_name = self._find_unicode_font()

    def _find_unicode_font(self):
        """Find the best available Unicode font."""
        # Ensure pygame font system is initialized
        if not pygame.font.get_init():
            pygame.font.init()

        available_fonts = pygame.font.get_fonts()

        # Test with two sets: basic arrows/symbols (small) and emoji (can be large)
        basic_chars = ["►", "◄", "↑", "↓", "✓", "→", "←"]
        emoji_chars = ["🐱", "🐈", "😸"]

        # First try fonts that we know exist on this system
        symbol_fonts = [font for font in available_fonts if "symbol" in font.lower()]

        # Expanded list of Unicode fonts to try, separating emoji from regular fonts
        regular_unicode_fonts = [
            "dejavusans",  # DejaVu Sans (usually has good unicode support)
            "dejavuserif",  # DejaVu Serif
            "liberation",  # Liberation fonts
            "liberationsans",  # Liberation Sans
            "noto",  # General Noto font
            "notosans",  # Noto Sans
            "notomono",  # Noto Mono
            "arial",  # Arial (has some unicode)
            "segoeuisymbol",  # Windows
            "fonts-seto",
            "notosanssymbols",  # Linux
            "notosanssymbols2",  # Alternative naming
            "opensymbol",  # LibreOffice symbol font
            "unifont",  # GNU Unifont (comprehensive Unicode coverage)
            "freesans",  # Free fonts
            "freeserif",  # Free fonts
        ] + symbol_fonts  # Add any symbol fonts we found

        emoji_fonts = [
            "notocoloremoji",  # Google's color emoji font
            "applecoloremoji",  # Apple's emoji font
            "seguiemj",  # Windows emoji font
            "twemoji",  # Twitter emoji font
        ]

        ### print(f"Available symbol fonts: {symbol_fonts}")
        ### print(f"Total available fonts: {len(available_fonts)}")

        # Test the default font first with basic characters only
        default_result = self._test_font_unicode_support(None, basic_chars)
        if default_result["score"] >= len(basic_chars):
            ### print(f"Default font works with basic Unicode (rendered {default_result['score']}/{len(basic_chars)} test chars)")
            ### print(f"Supported chars: {default_result['supported']}")
            return {
                "name": "default",
                "supported_chars": set(default_result["supported"]),
            }

        # Test regular Unicode fonts with basic characters
        for font_name in regular_unicode_fonts:
            if font_name in available_fonts:
                result = self._test_font_unicode_support(font_name, basic_chars)

                if result["score"] == len(basic_chars):
                    ### print(f"Using Unicode font: {font_name} (rendered {result['score']}/{len(basic_chars)} basic chars)")
                    ### print(f"Supported chars: {result['supported']}")
                    return {
                        "name": font_name,
                        "supported_chars": set(result["supported"]),
                    }
                else:
                    ### print(f"Font {font_name} only rendered {result['score']}/{len(basic_chars)} basic chars, skipping")
                    pass

        # If no regular font works well, try emoji fonts (but they might be problematic)
        # print("No good regular Unicode font found, trying emoji fonts...")
        for font_name in emoji_fonts:
            if font_name in available_fonts:
                result = self._test_font_unicode_support(
                    font_name, basic_chars + emoji_chars
                )

                if result["score"] >= len(
                    basic_chars
                ):  # At least the basic chars should work
                    # print(f"Using emoji font: {font_name} (rendered {result['score']}/{len(basic_chars + emoji_chars)} total chars)")
                    # print(f"Supported chars: {result['supported']}")
                    # print("WARNING: Emoji fonts may render very large characters")
                    return {
                        "name": font_name,
                        "supported_chars": set(result["supported"]),
                    }

        print("No suitable Unicode font found, using ASCII fallbacks")
        return None

    def _test_font_unicode_support(self, font_name, test_chars):
        """
        Test a font's Unicode support by attempting to render test characters.

        Returns:
            dict: {
                'score': int,  # Number of successfully rendered characters
                'supported': list,  # List of successfully rendered characters
                'failed': list  # List of characters that failed or rendered as tofu
            }
        """
        supported = []
        failed = []

        try:
            # Create font for testing
            if font_name is None:
                test_font = pygame.font.Font(None, 16)
            else:
                try:
                    test_font = pygame.font.SysFont(font_name, 16)
                except:
                    try:
                        font_path = pygame.font.match_font(font_name)
                        if font_path:
                            test_font = pygame.font.Font(font_path, 16)
                        else:
                            return {"score": 0, "supported": [], "failed": test_chars}
                    except:
                        return {"score": 0, "supported": [], "failed": test_chars}

            # Test each character using a more sophisticated approach
            for char in test_chars:
                if self._can_font_render_char(test_font, char, font_name or "default"):
                    supported.append(char)
                else:
                    failed.append(char)

        except Exception as e:
            print(f"Error testing font {font_name}: {e}")
            return {"score": 0, "supported": [], "failed": test_chars}

        return {"score": len(supported), "supported": supported, "failed": failed}

    def _can_font_render_char(self, font, char, font_name):
        """
        Test if a font can properly render a specific character.

        Uses multiple heuristics to detect proper rendering vs tofu.
        """
        try:
            # Render the character
            char_surface = font.render(char, True, (255, 255, 255))
            char_width = char_surface.get_width()
            char_height = char_surface.get_height()

            # Basic sanity checks
            if char_width <= 1 or char_height <= 1:
                return False

            # For emoji, expect larger sizes
            if ord(char) >= 0x1F000:  # Emoji Unicode range starts around here
                if char_width < 8 or char_height < 8:
                    return False

            # For arrow/symbol characters, expect reasonable width
            elif char in ["►", "◄", "↑", "↓", "✓", "→", "←"]:
                if char_width < 3:
                    return False

            # Test by comparing against known missing character
            try:
                # Render a character that definitely doesn't exist
                missing_char = font.render(
                    "\ue000", True, (255, 255, 255)
                )  # Private use area
                missing_width = missing_char.get_width()

                # If our character has the same width as the missing char and is very narrow,
                # it's probably rendering as the same replacement glyph
                if char_width == missing_width and char_width <= 6:
                    return False
            except:
                pass

            # Character passed all tests
            return True

        except Exception:
            return False

    def _get_font(self, font_name, size):
        """Get a font from cache or create it."""
        cache_key = (font_name, size)
        if cache_key not in self.font_cache:
            try:
                if font_name is None:
                    # Use default font
                    self.font_cache[cache_key] = pygame.font.Font(None, size)
                else:
                    # Try SysFont first
                    try:
                        self.font_cache[cache_key] = pygame.font.SysFont(
                            font_name, size
                        )
                        ### print(f"Successfully loaded font: {font_name} at size {size}")
                    except Exception as e:
                        ### print(f"SysFont failed for {font_name}: {e}")
                        # Try finding font file path
                        font_path = pygame.font.match_font(font_name)
                        if font_path:
                            self.font_cache[cache_key] = pygame.font.Font(
                                font_path, size
                            )
                            ### print(f"Successfully loaded font from path: {font_path} at size {size}")
                        else:
                            # Fall back to default font
                            ### print(f"Could not load font {font_name}, using default")
                            self.font_cache[cache_key] = pygame.font.Font(None, size)
            except Exception as e:
                ### print(f"Error creating font {font_name}: {e}, using default")
                self.font_cache[cache_key] = pygame.font.Font(None, size)

        return self.font_cache[cache_key]

    def render_text_mixed(self, text, size, color, surface, position, center=False):
        """
        Render text with mixed font support for Unicode characters.

        Args:
            text: The text to render
            size: Font size
            color: Text color
            surface: Surface to render onto
            position: (x, y) position tuple
            center: If True, center the text at the position

        Returns:
            pygame.Rect of the rendered text area
        """
        regular_font = self._get_font(None, size)  # Default system font

        # Handle unicode font selection
        if self.unicode_font_name and isinstance(self.unicode_font_name, dict):
            # New format with supported character set
            font_info = self.unicode_font_name
            if font_info["name"] == "default":
                unicode_font = regular_font
            else:
                unicode_font = self._get_font(font_info["name"], size)
            supported_chars = font_info["supported_chars"]
        elif self.unicode_font_name == "default":
            # Legacy format - assume all characters work
            unicode_font = regular_font
            supported_chars = set(
                ["►", "◄", "↑", "↓", "✓", "→", "←", "🐱", "🐈", "😸"]
            )  # Assume basic set works
        elif self.unicode_font_name:
            # Legacy named font
            unicode_font = self._get_font(self.unicode_font_name, size)
            supported_chars = set(
                ["►", "◄", "↑", "↓", "✓", "→", "←"]
            )  # Conservative assumption
        else:
            # No Unicode support available
            unicode_font = None
            supported_chars = set()

        if not unicode_font:
            # No unicode font available, use simple fallback
            return self.render_text_simple(
                text, size, color, surface, position, center, unicode_fallback=True
            )

        # Convert to string in case we get non-string input
        text = str(text)

        # Calculate total width for centering if needed
        if center:
            total_width = self._calculate_text_width(
                text, regular_font, unicode_font, supported_chars
            )
            x = position[0] - total_width // 2
            y = position[1]
        else:
            x, y = position

        current_x = x
        total_width = 0
        max_height = 0

        # Get baseline information for alignment
        regular_metrics = regular_font.get_ascent()
        unicode_metrics = unicode_font.get_ascent()

        for char in text:
            # Check if character is unicode (outside ASCII range)
            if ord(char) > 127:
                # Use whitelist approach instead of tofu detection
                if char in supported_chars:
                    # Character is known to work with this font
                    try:
                        char_surface = unicode_font.render(char, True, color)
                        ### print(f"Rendered Unicode char '{char}' successfully with {font_info['name'] if isinstance(self.unicode_font_name, dict) else 'legacy font'}")
                        # Unicode rendered properly
                        if unicode_font == regular_font:
                            # Same font, no baseline adjustment needed
                            char_y = y
                        else:
                            # Different fonts, adjust Y position to align baselines
                            baseline_adjustment = regular_metrics - unicode_metrics

                            # For arrows and symbols, add subtle vertical centering adjustment
                            if char in ["►", "◄", "↑", "↓", "→", "←"]:
                                char_height = char_surface.get_height()
                                regular_height = regular_font.get_height()
                                # Use a smaller fraction for more subtle adjustment
                                vertical_center_adjustment = (
                                    abs(regular_height - char_height) // 4
                                )  ###
                                baseline_adjustment += vertical_center_adjustment

                            char_y = y + baseline_adjustment
                    except Exception as e:
                        ### print(f"Unicode rendering failed for '{char}': {e}, using ASCII fallback")
                        # Unicode rendering failed, use ASCII fallback
                        fallback_char = self._get_ascii_fallback(char)
                        char_surface = regular_font.render(fallback_char, True, color)
                        char_y = y
                else:
                    # Character not in whitelist, use ASCII fallback
                    fallback_char = self._get_ascii_fallback(char)
                    char_surface = regular_font.render(fallback_char, True, color)
                    char_y = y
                    ### print(f"Char '{char}' not in whitelist, using fallback '{fallback_char}'")
            else:
                # Use regular font for ASCII characters
                char_surface = regular_font.render(char, True, color)
                char_y = y

            surface.blit(char_surface, (current_x, char_y))
            char_width = char_surface.get_width()
            char_height = char_surface.get_height()

            current_x += char_width
            total_width += char_width
            max_height = max(max_height, char_height)

        return pygame.Rect(x, y, total_width, max_height)

    def _calculate_text_width(
        self, text, regular_font, unicode_font, supported_chars=None
    ):
        """Calculate the total width of text with mixed fonts."""
        total_width = 0
        if supported_chars is None:
            supported_chars = set()

        for char in text:
            if ord(char) > 127 and unicode_font and char in supported_chars:
                char_width = unicode_font.size(char)[0]
            else:
                char_width = regular_font.size(char)[0]
            total_width += char_width
        return total_width

    def render_text_simple(
        self, text, size, color, surface, position, center=False, unicode_fallback=True
    ):
        """
        Render text with simple fallback for Unicode characters.

        Args:
            text: The text to render
            size: Font size
            color: Text color
            surface: Surface to render onto
            position: (x, y) position tuple
            center: If True, center the text at the position
            unicode_fallback: If True, replace unicode with ASCII fallbacks

        Returns:
            pygame.Rect of the rendered text area
        """
        regular_font = self._get_font(None, size)

        # Replace common Unicode characters with ASCII equivalents if fallback is enabled
        if unicode_fallback:
            fallback_text = (
                text.replace("►", ">")
                .replace("◄", "<")
                .replace("↑", "^")
                .replace("↓", "v")
                .replace("→", ">")
                .replace("←", "<")
                .replace("✓", "OK")
                .replace("✗", "X")
            )
        else:
            fallback_text = text

        # Convert to string in case we get non-string input
        fallback_text = str(fallback_text)

        rendered_text = regular_font.render(fallback_text, True, color)

        if center:
            rect = rendered_text.get_rect(center=position)
            surface.blit(rendered_text, rect)
            return rect
        else:
            surface.blit(rendered_text, position)
            return pygame.Rect(
                position[0],
                position[1],
                rendered_text.get_width(),
                rendered_text.get_height(),
            )

    def render_unicode_char(
        self, char, size, color, surface, position, center=False, fallback_char=None
    ):
        """
        Render a single Unicode character with proper alignment.

        Args:
            char: The Unicode character to render
            size: Font size
            color: Text color
            surface: Surface to render onto
            position: (x, y) position tuple
            center: If True, center the character at the position
            fallback_char: ASCII character to use if Unicode fails

        Returns:
            pygame.Rect of the rendered character area
        """
        # Use whitelist approach instead of tofu detection
        if self.unicode_font_name:
            if isinstance(self.unicode_font_name, dict):
                # New format with supported character set
                font_info = self.unicode_font_name
                ### print(f"Trying to render Unicode char '{char}' with font '{font_info['name']}'")
                ### print(f"Character in whitelist: {char in font_info['supported_chars']}")
                if char in font_info["supported_chars"]:
                    try:
                        if font_info["name"] == "default":
                            font = self._get_font(None, size)
                        else:
                            font = self._get_font(font_info["name"], size)

                        # Character is known to work, render it
                        char_surface = font.render(char, True, color)
                        ### print(f"Successfully rendered Unicode char '{char}' with size {char_surface.get_width()}x{char_surface.get_height()}")

                        # Calculate vertical alignment adjustment for better centering
                        regular_font = self._get_font(None, size)
                        if font != regular_font:
                            # Different fonts - adjust for baseline differences
                            regular_metrics = regular_font.get_ascent()
                            unicode_metrics = font.get_ascent()
                            baseline_adjustment = regular_metrics - unicode_metrics

                            # For arrows and symbols, apply a subtle centering adjustment
                            if char in ["►", "◄", "↑", "↓", "→", "←"]:
                                # Small vertical adjustment for better alignment with text baseline
                                char_height = char_surface.get_height()
                                regular_height = regular_font.get_height()
                                # Use a smaller fraction for more subtle adjustment
                                vertical_center_adjustment = (
                                    abs(regular_height - char_height) // 4
                                )  ###
                                baseline_adjustment += vertical_center_adjustment
                        else:
                            baseline_adjustment = 0

                        if center:
                            rect = char_surface.get_rect(center=position)
                            rect.y += baseline_adjustment
                            surface.blit(char_surface, rect)
                            return rect
                        else:
                            adjusted_position = (
                                position[0],
                                position[1] + baseline_adjustment,
                            )
                            surface.blit(char_surface, adjusted_position)
                            return pygame.Rect(
                                adjusted_position[0],
                                adjusted_position[1],
                                char_surface.get_width(),
                                char_surface.get_height(),
                            )
                    except Exception as e:
                        ### print(f"Exception rendering Unicode char '{char}': {e}")
                        pass
            else:
                # Legacy format - try to render but be conservative
                try:
                    if self.unicode_font_name == "default":
                        font = self._get_font(None, size)
                    else:
                        font = self._get_font(self.unicode_font_name, size)

                    # Only try common symbols in legacy mode
                    if char in ["►", "◄", "↑", "↓", "✓", "→", "←"]:
                        char_surface = font.render(char, True, color)

                        # Apply baseline adjustment for legacy mode too
                        regular_font = self._get_font(None, size)
                        if font != regular_font:
                            regular_metrics = regular_font.get_ascent()
                            unicode_metrics = font.get_ascent()
                            baseline_adjustment = regular_metrics - unicode_metrics

                            if char in ["►", "◄", "↑", "↓", "→", "←"]:
                                char_height = char_surface.get_height()
                                regular_height = regular_font.get_height()
                                # Use a smaller fraction for more subtle adjustment
                                vertical_center_adjustment = (
                                    abs(regular_height - char_height) // 4
                                )  ###
                                baseline_adjustment += vertical_center_adjustment
                        else:
                            baseline_adjustment = 0

                        if center:
                            rect = char_surface.get_rect(center=position)
                            rect.y += baseline_adjustment
                            surface.blit(char_surface, rect)
                            return rect
                        else:
                            adjusted_position = (
                                position[0],
                                position[1] + baseline_adjustment,
                            )
                            surface.blit(char_surface, adjusted_position)
                            return pygame.Rect(
                                adjusted_position[0],
                                adjusted_position[1],
                                char_surface.get_width(),
                                char_surface.get_height(),
                            )
                except:
                    pass

        # Fall back to ASCII
        fallback = fallback_char or self._get_ascii_fallback(char)
        regular_font = self._get_font(None, size)
        char_surface = regular_font.render(fallback, True, color)

        if center:
            rect = char_surface.get_rect(center=position)
            surface.blit(char_surface, rect)
            return rect
        else:
            surface.blit(char_surface, position)
            return pygame.Rect(
                position[0],
                position[1],
                char_surface.get_width(),
                char_surface.get_height(),
            )

    def _get_ascii_fallback(self, unicode_char):
        """Get ASCII fallback for common Unicode characters."""
        fallbacks = {
            "►": ">",
            "◄": "<",
            "↑": "^",
            "↓": "v",
            "→": ">",
            "←": "<",
            "✓": "OK",
            "✗": "X",
            "☑": "[v]",
            "☐": "[ ]",
        }
        return fallbacks.get(unicode_char, "?")


# Global text renderer instance
text_renderer = TextRenderer()


def render_text(surface, text, position, size, color, center=False, right_align=False):
    """
    Convenience function for rendering text with the global text renderer.

    Args:
        surface: Surface to render onto
        text: The text to render
        position: (x, y) position tuple - Y is always the top of the text
        size: Font size
        color: Text color
        center: If True, center the text horizontally at the X position
        right_align: If True, right-align the text at the X position

    Returns:
        pygame.Rect of the rendered text area
    """
    # Convert to string in case we get non-string input
    text = str(text)

    # Get font to calculate text dimensions
    font = text_renderer._get_font(None, size)
    text_width = font.size(text)[0]

    if right_align:
        # Right-align: position X is the right edge of the text
        adjusted_position = (position[0] - text_width, position[1])
    elif center:
        # Center: position X is the center of the text
        adjusted_position = (position[0] - text_width // 2, position[1])
    else:
        # Left-align: position X is the left edge of the text
        adjusted_position = position

    # Always use left-aligned rendering with adjusted position
    return text_renderer.render_text_simple(
        text, size, color, surface, adjusted_position, center=False
    )


def run_font_diagnostics():
    """Run font capability diagnostics using the global text renderer."""
    return text_renderer.test_font_capabilities()


def quick_unicode_test():
    """Quick test to see what Unicode font is being used and test a few characters."""
    if not pygame.font.get_init():
        pygame.font.init()

    print(f"=== Quick Unicode Test ===")
    print(f"Unicode font name: {text_renderer.unicode_font_name}")

    test_chars = ["►", "◄", "↑", "↓", "✓"]

    # Test the actual font being used
    if text_renderer.unicode_font_name == "default":
        font = pygame.font.Font(None, 16)
        print("Using default font for Unicode")
    elif text_renderer.unicode_font_name:
        try:
            font = pygame.font.SysFont(text_renderer.unicode_font_name, 16)
            print(f"Using named font: {text_renderer.unicode_font_name}")
        except:
            font = pygame.font.Font(None, 16)
            print("Named font failed, using default")
    else:
        font = pygame.font.Font(None, 16)
        print("No Unicode font, using default")

    for char in test_chars:
        try:
            rendered = font.render(char, True, (255, 255, 255))
            width = rendered.get_width()
            print(
                f"  '{char}': width={width} {'✓' if width >= 5 else '✗ (likely tofu)'}"
            )
        except Exception as e:
            print(f"  '{char}': ERROR - {e}")

    print("=== End Quick Test ===\n")
