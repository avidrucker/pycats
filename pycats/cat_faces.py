"""
Purpose: Selectable cat-face render styles (#108) — a debug/test harness to
compare face options live in-game (toggled with the E / ; keys). Render-only:
the default (primitives) is unchanged, so the sim, goldens, and existing render
tests are unaffected.

Styles (#114): primitives (current) · ASCII profile head (flipped to face the
opponent) · ASCII 3/4 head. The two ASCII heads are the pure-ASCII #110 designs
— head-only, tintable, no emoji/font-art dependency — drawn by a multi-line
monospace block renderer. They fall back to None (→ caller draws primitives)
when no monospace font is available. The retired kaomoji/emoji glyph styles
(`ᓚᘏᗢ` / `(=^･ω･^=)` / `🐱`) are gone (#114, superseding #103/#105).
"""
import pygame  # type: ignore

PRIMITIVES, ASCII_PROFILE, ASCII_34 = 0, 1, 2
FACE_STYLES = ("primitives", "profile", "3/4")

# Pure-ASCII head art from #110. Profile is authored facing RIGHT (mirrored for
# the left-facing fighter); the 3/4 head is symmetric, so it never flips.
_ASCII_PROFILE_LINES = (
    r" /\___",
    r"( o   >",
    r" \___>",
)
_ASCII_34_LINES = (
    r" /\_/\ ",
    r"( o.o )",
    r"  >^<  ",
)
_ASCII_ART = {
    ASCII_PROFILE: _ASCII_PROFILE_LINES,
    ASCII_34: _ASCII_34_LINES,
}

_FACE_W = 46  # target face width in px (scaled to fit the ~40-wide body)
# Rendered large then smoothscaled down to _FACE_W, so the 3-line head stays
# legible at the ~40px body size (#110 legibility caveat).
_MONO_SIZE = 28
_MONO_FONTS = (
    "dejavusansmono", "liberationmono", "freemono",
    "couriernew", "consolas", "menlo", "monospace",
)

_font_cache: dict = {}


def cycle_face_style(idx):
    """Next style index, wrapping (primitives -> profile -> 3/4 -> ...)."""
    return (idx + 1) % len(FACE_STYLES)


def ink_for(body_color):
    """A contrasting 'ink' colour for the face so it reads on the body (the body
    fill already carries the per-cat colour identity): dark ink on a light cat,
    light ink on a dark cat."""
    r, g, b = body_color[:3]
    luminance = 0.299 * r + 0.587 * g + 0.114 * b
    return (25, 25, 25) if luminance > 110 else (235, 235, 235)


def face_style_label(idx):
    """Human label for a style index (bounds-safe)."""
    if 0 <= idx < len(FACE_STYLES):
        return FACE_STYLES[idx]
    return FACE_STYLES[0]


def _mono_font(size):
    """A monospace `pygame.font.Font` at `size`, or None when the host has no
    monospace face (the caller then falls back to the primitive face)."""
    f = _font_cache.get(size, "miss")
    if f == "miss":
        f = None
        for name in _MONO_FONTS:
            path = pygame.font.match_font(name)
            if path:
                f = pygame.font.Font(path, size)
                break
        _font_cache[size] = f
    return f


def _render_ascii_block(lines, color):
    """Stack `lines` of monospace text into one transparent surface, inked
    `color`. Returns None when no monospace font is available."""
    font = _mono_font(_MONO_SIZE)
    if font is None:
        return None
    linesize = font.get_linesize()
    rendered = [font.render(line, True, color) for line in lines]
    w = max((s.get_width() for s in rendered), default=0)
    h = linesize * len(rendered)
    if w == 0 or h == 0:
        return None
    block = pygame.Surface((w, h), pygame.SRCALPHA)
    for i, s in enumerate(rendered):
        block.blit(s, (0, i * linesize))
    return block


def render_face(style, facing_right, color):
    """Surface for the given face `style`, scaled to the face width, inked
    `color`, and oriented to `facing_right`. Returns None for primitives, an
    unknown style, or when no monospace font can render the ASCII head — the
    caller then draws the primitive face.
    """
    lines = _ASCII_ART.get(style)
    if lines is None:
        return None
    block = _render_ascii_block(lines, color)
    if block is None:
        return None
    w, h = block.get_size()
    scale = _FACE_W / w
    surf = pygame.transform.smoothscale(
        block, (max(1, round(w * scale)), max(1, round(h * scale)))
    )
    # The profile head is authored facing RIGHT; mirror it for a left-facing
    # fighter so the two cats face each other.
    if style == ASCII_PROFILE and not facing_right:
        surf = pygame.transform.flip(surf, True, False)
    return surf
