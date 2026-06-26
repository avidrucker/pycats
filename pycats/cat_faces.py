"""
Purpose: Selectable cat-face render styles (#108) — a debug/test harness to
compare the face options from the #103/#105 research live in-game (toggled with
the E / ; keys). Render-only: the default (primitives) is unchanged, so the sim,
goldens, and existing render tests are unaffected.

Styles: primitives (current) · sideways profile kaomoji (ᓚᘏᗢ, flipped to face) ·
front kaomoji ((=^･ω･^=)) · colour emoji (🐱, font-gated). Glyph styles fall back
to None (→ caller draws primitives) when the needed font/glyph is unavailable.
"""
import pygame  # type: ignore

PRIMITIVES, SIDEWAYS, FRONT, EMOJI = 0, 1, 2, 3
FACE_STYLES = ("primitives", "sideways", "front", "emoji")

# glyph text + the fonts to try (first that renders it non-blank wins)
_GLYPHS = {
    SIDEWAYS: ("ᓚᘏᗢ", ("notosanscanadianaboriginal", "dejavusans", None)),
    FRONT: ("(=^･ω･^=)", ("notosanscanadianaboriginal", "dejavusans", "notosans", None)),
    EMOJI: ("\U0001F431", ("notocoloremoji",)),
}
_FACE_W = 46  # target face width in px (scaled to fit the ~40-wide body)

_font_cache: dict = {}


def cycle_face_style(idx):
    """Next style index, wrapping (primitives -> sideways -> front -> emoji -> ...)."""
    return (idx + 1) % len(FACE_STYLES)


def ink_for(body_color):
    """A contrasting 'ink' colour for the face glyph so it reads on the body
    (the body fill already carries the per-cat colour identity): dark ink on a
    light cat, light ink on a dark cat."""
    r, g, b = body_color[:3]
    luminance = 0.299 * r + 0.587 * g + 0.114 * b
    return (25, 25, 25) if luminance > 110 else (235, 235, 235)


def face_style_label(idx):
    """Human label for a style index (bounds-safe)."""
    if 0 <= idx < len(FACE_STYLES):
        return FACE_STYLES[idx]
    return FACE_STYLES[0]


def _font(name, size):
    f = _font_cache.get((name, size))
    if f is None:
        f = pygame.font.SysFont(name, size)
        _font_cache[(name, size)] = f
    return f


def _is_opaque(surf):
    w, h = surf.get_size()
    return any(surf.get_at((x, y))[3] > 10 for y in range(0, h, 2) for x in range(0, w, 2))


def render_face(style, facing_right, color):
    """Surface for the given face `style`, scaled to the face width, tinted
    `color` (ignored by colour emoji), and oriented to `facing_right`. Returns
    None for primitives, an unknown style, or when the glyph can't be rendered —
    the caller then draws the primitive face.
    """
    if style not in _GLYPHS:
        return None
    text, fonts = _GLYPHS[style]
    size = 96 if style == EMOJI else 34
    surf = None
    for name in fonts:
        candidate = _font(name, size).render(text, True, color)
        if candidate.get_width() > 0 and candidate.get_height() > 0 and _is_opaque(candidate):
            surf = candidate
            break
    if surf is None:
        return None
    w, h = surf.get_size()
    scale = _FACE_W / w
    surf = pygame.transform.smoothscale(surf, (max(1, round(w * scale)), max(1, round(h * scale))))
    # The profile face is authored facing RIGHT; flip it when the fighter faces left.
    if style == SIDEWAYS and not facing_right:
        surf = pygame.transform.flip(surf, True, False)
    return surf
