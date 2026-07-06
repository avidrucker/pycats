"""render_text_mixed caches composed text surfaces (#372).

The freeze root cause: render_text_mixed re-rasterised text glyph-by-glyph every
frame (no cache) — ~58 font.render() calls per main-menu frame on static text,
a per-glyph SDL_ttf storm that hard-hangs the menus on a real display. The fix
composes each (text,size,colour) once onto an intermediate surface and blits the
cached surface thereafter. Output must stay byte-identical (glyphs are
non-overlapping side-by-side blits, so one-step vs two-step compositing match).
"""


import pygame  # noqa: E402

from pycats.text_utils import TextRenderer  # noqa: E402


def _tr():
    pygame.font.init()
    return TextRenderer()


def _direct_blit_reference(tr, text, size, color, surface, position, center):
    """Faithful copy of the OLD per-char direct-blit algorithm, for byte-parity.

    Mirrors the pre-#372 render_text_mixed loop exactly so the cached path can be
    proven pixel-identical to it."""
    regular_font = tr._get_font(None, size)
    font_info = tr.unicode_font_name
    assert isinstance(font_info, dict) and font_info["name"] != "default", (
        "reference assumes the common dict-with-named-font config")
    unicode_font = tr._get_font(font_info["name"], size)
    supported = font_info["supported_chars"]
    text = str(text)
    if center:
        total = tr._calculate_text_width(text, regular_font, unicode_font, supported)
        x = position[0] - total // 2
    else:
        x = position[0]
    y = position[1]
    cur_x = x
    reg_asc = regular_font.get_ascent()
    uni_asc = unicode_font.get_ascent()
    for char in text:
        if ord(char) > 127:
            if char in supported:
                try:
                    cs = unicode_font.render(char, True, color)
                    if unicode_font == regular_font:
                        cy = y
                    else:
                        adj = reg_asc - uni_asc
                        if char in ["►", "◄", "↑", "↓", "→", "←"]:
                            adj += abs(regular_font.get_height() - cs.get_height()) // 4
                        cy = y + adj
                except Exception:
                    cs = regular_font.render(tr._get_ascii_fallback(char), True, color)
                    cy = y
            else:
                cs = regular_font.render(tr._get_ascii_fallback(char), True, color)
                cy = y
        else:
            cs = regular_font.render(char, True, color)
            cy = y
        surface.blit(cs, (cur_x, cy))
        cur_x += cs.get_width()


def test_repeated_render_composes_only_once():
    tr = _tr()
    s = pygame.Surface((500, 80))
    txt = "Use W/S or ↑/↓ to navigate"
    tr.render_text_mixed(txt, 20, (255, 255, 255), s, (250, 40), center=True)
    first = tr.mixed_cache_misses
    for _ in range(30):
        tr.render_text_mixed(txt, 20, (255, 255, 255), s, (250, 40), center=True)
    assert first == 1
    assert tr.mixed_cache_misses == first  # 30 more renders, zero new compositions


def test_distinct_key_recomposes():
    tr = _tr()
    s = pygame.Surface((400, 80))
    tr.render_text_mixed("Play", 24, (255, 0, 0), s, (200, 40))
    m = tr.mixed_cache_misses
    tr.render_text_mixed("Play", 24, (0, 255, 0), s, (200, 40))   # new colour
    tr.render_text_mixed("Quit", 24, (255, 0, 0), s, (200, 40))   # new text
    assert tr.mixed_cache_misses == m + 2


def test_cached_output_is_byte_identical_to_direct_blit():
    for txt, center in [("Use W/S or ↑/↓ to navigate", True),
                        ("Options ► ON", True),
                        ("Status Bars: ON", False)]:
        tr = _tr()
        a = pygame.Surface((520, 90))
        a.fill((10, 10, 20))
        b = pygame.Surface((520, 90))
        b.fill((10, 10, 20))
        tr.render_text_mixed(txt, 24, (255, 255, 0), a, (260, 40), center=center)
        _direct_blit_reference(tr, txt, 24, (255, 255, 0), b, (260, 40), center)
        assert pygame.image.tobytes(a, "RGBA") == pygame.image.tobytes(b, "RGBA"), txt
