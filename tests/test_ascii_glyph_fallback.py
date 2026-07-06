"""render_text_mixed substitutes a legible ASCII stand-in — never "?" — for
arrow/marker glyphs when the selected font can't render them (#547).

`_find_unicode_font` logs "using ASCII fallbacks" when no font covers the probe
glyphs, and `_compose_mixed` routes any font-unsupported glyph through
`_get_ascii_fallback`. This drives BOTH degraded paths render_text_mixed can take:

  A. no unicode font at all      (unicode_font_name -> None; render_text_simple)
  B. a font present but the glyph unsupported (dict + empty supported_chars;
     render_text_mixed -> _compose_mixed -> _get_ascii_fallback)

and asserts each known symbol renders as its ASCII substitute, not "?" and not
tofu. Able-to-fail: revert a map entry (or drop ▶ from the map / the
render_text_simple replace chain) and the glyph falls back to "?"/tofu → red.
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

from pycats.text_utils import TextRenderer  # noqa: E402

# glyph -> the legible ASCII stand-in it must degrade to (#547 Should table;
# ✓ stays "OK" — a confirmation marker, so "P1 ✓" -> "P1 OK", never "P1 x").
SUBSTITUTIONS = {
    "►": ">",
    "▶": ">",
    "◄": "<",
    "→": ">",
    "←": "<",
    "↑": "^",
    "↓": "v",
    "✓": "OK",
}

_SIZE = 24
_COLOR = (255, 255, 255)


def _tr():
    pygame.font.init()
    return TextRenderer()


def _mixed_bytes(tr, text):
    """Drive render_text_mixed and return the rendered glyph region's raw bytes."""
    surf = pygame.Surface((400, 80), pygame.SRCALPHA)
    rect = tr.render_text_mixed(text, _SIZE, _COLOR, surf, (0, 0))
    region = surf.subsurface(pygame.Rect(0, 0, rect.width, rect.height))
    return region.get_buffer().raw


def _ascii_bytes(tr, ascii_str):
    """Reference bytes: the regular font's render of an ASCII string, laid out the
    same way render_text_mixed lays out a single substituted run."""
    glyph = tr._get_font(None, _SIZE).render(ascii_str, True, _COLOR)
    surf = pygame.Surface((400, 80), pygame.SRCALPHA)
    surf.blit(glyph, (0, 0))
    region = surf.subsurface(pygame.Rect(0, 0, glyph.get_width(), glyph.get_height()))
    return region.get_buffer().raw


def _degraded_no_font():
    tr = _tr()
    tr.unicode_font_name = None  # _find_unicode_font found nothing (path A)
    return tr


def _degraded_unsupported():
    tr = _tr()
    # A font is selected, but it covers none of the probe glyphs (path B).
    tr.unicode_font_name = {"name": "default", "supported_chars": set()}
    return tr


def test_no_unicode_font_substitutes_every_symbol():
    tr = _degraded_no_font()
    qmark = _ascii_bytes(tr, "?")
    for glyph, ascii_sub in SUBSTITUTIONS.items():
        got = _mixed_bytes(tr, glyph)
        assert got == _ascii_bytes(tr, ascii_sub), f"{glyph!r} should render as {ascii_sub!r} (no-font path)"
        assert got != qmark, f"{glyph!r} rendered as '?' on the no-font path"


def test_unsupported_glyph_substitutes_every_symbol():
    tr = _degraded_unsupported()
    qmark = _ascii_bytes(tr, "?")
    for glyph, ascii_sub in SUBSTITUTIONS.items():
        got = _mixed_bytes(tr, glyph)
        assert got == _ascii_bytes(tr, ascii_sub), f"{glyph!r} should render as {ascii_sub!r} (unsupported-glyph path)"
        assert got != qmark, f"{glyph!r} rendered as '?' on the unsupported-glyph path"


def test_get_ascii_fallback_maps_the_should_table():
    tr = _tr()
    for glyph, ascii_sub in SUBSTITUTIONS.items():
        assert tr._get_ascii_fallback(glyph) == ascii_sub, f"{glyph!r} map entry"
