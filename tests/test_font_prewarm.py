"""`_get_font` takes no runtime SysFont/match_font miss path for a new size (#1264 / B1).

`TextRenderer._get_font(name, size)` caches by (name, size). Before #1264, a cache
miss on a *named* font called ``pygame.font.SysFont(name, size)`` (a fontconfig
lookup that hard-hangs on an on-screen display, #375) — every distinct size a fresh miss,
so a font_scale change bursts SysFont/match_font builds. After #1264 the font path is
resolved once per name and each size is built with ``pygame.font.Font(path, size)``,
so a new size takes no SysFont/match_font call. The substitution is pixel-identical:
``SysFont(name, size)`` with no bold/italic is ``Font(match_font(name), size)``.
"""

import pygame  # noqa: E402
import pygame.image  # noqa: E402

from pycats.ui.text_utils import TextRenderer  # noqa: E402


def _real_named_font():
    """A font name that ``match_font`` resolves to a path, or None if none exist."""
    pygame.font.init()
    for preferred in ("dejavusans", "liberationsans", "freesans"):
        if pygame.font.match_font(preferred):
            return preferred
    for name in pygame.font.get_fonts():
        if pygame.font.match_font(name):
            return name
    return None


def _spy(monkeypatch, attr):
    calls = {"n": 0}
    orig = getattr(pygame.font, attr)

    def spy(*a, **k):
        calls["n"] += 1
        return orig(*a, **k)

    monkeypatch.setattr(pygame.font, attr, spy)
    return calls


def test_new_size_after_warmup_takes_no_sysfont_or_matchfont_miss_path(monkeypatch):
    name = _real_named_font()
    assert name is not None, "no resolvable system font available for the test"

    tr = TextRenderer()
    tr._get_font(name, 24)  # warm: resolve + cache the path for this name

    sysfont = _spy(monkeypatch, "SysFont")
    matchfont = _spy(monkeypatch, "match_font")
    font = tr._get_font(name, 30)  # a NEW size

    assert isinstance(font, pygame.font.Font)
    assert sysfont["n"] == 0  # no fontconfig SysFont build mid-run
    assert matchfont["n"] == 0  # path already resolved; not re-looked-up per size


def test_get_font_named_pixel_identical_to_sysfont():
    name = _real_named_font()
    assert name is not None, "no resolvable system font available for the test"

    tr = TextRenderer()
    got = tr._get_font(name, 24).render("Damage 42%", True, (255, 255, 255))
    ref = pygame.font.SysFont(name, 24).render("Damage 42%", True, (255, 255, 255))

    assert got.get_size() == ref.get_size()
    assert pygame.image.tobytes(got, "RGBA") == pygame.image.tobytes(ref, "RGBA")
