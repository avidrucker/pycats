"""render_text_mixed caches composed text surfaces (#372).

The freeze root cause: render_text_mixed re-rasterised text glyph-by-glyph every
frame (no cache) — ~58 font.render() calls per main-menu frame on static text,
a per-glyph SDL_ttf storm that hard-hangs the menus on a real display. The fix
composes each (text,size,colour) once onto an intermediate surface and blits the
cached surface thereafter. Output must stay byte-identical (glyphs are
non-overlapping side-by-side blits, so one-step vs two-step compositing match).
"""

import pygame  # noqa: E402

from pycats.ui.text_utils import TextRenderer  # noqa: E402


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
        "reference assumes the common dict-with-named-font config"
    )
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
    tr.render_text_mixed("Play", 24, (0, 255, 0), s, (200, 40))  # new colour
    tr.render_text_mixed("Quit", 24, (255, 0, 0), s, (200, 40))  # new text
    assert tr.mixed_cache_misses == m + 2


def test_cached_output_is_byte_identical_to_direct_blit():
    for txt, center in [("Use W/S or ↑/↓ to navigate", True), ("Options ► ON", True), ("Status Bars: ON", False)]:
        tr = _tr()
        a = pygame.Surface((520, 90))
        a.fill((10, 10, 20))
        b = pygame.Surface((520, 90))
        b.fill((10, 10, 20))
        tr.render_text_mixed(txt, 24, (255, 255, 0), a, (260, 40), center=center)
        _direct_blit_reference(tr, txt, 24, (255, 255, 0), b, (260, 40), center)
        assert pygame.image.tobytes(a, "RGBA") == pygame.image.tobytes(b, "RGBA"), txt


# --- mixed cache LRU eviction (#1267 — B5) ----------------------------------


def test_mixed_cache_lru_keeps_still_visible_key_at_cap():
    """At cap, a still-visible (re-accessed) key survives eviction (#1267).

    The old code did a wholesale `clear()` at cap, so a live HUD/menu key was
    dropped alongside the dynamic churn and recomposed the next frame — a periodic
    hitch. LRU eviction (evict oldest, move-to-end on access) must keep the still-
    visible key. Able to fail: under wholesale-clear the final live render is a miss.
    """
    tr = _tr()
    tr._MIXED_CACHE_CAP = 8
    s = pygame.Surface((400, 80))

    def render(txt):
        tr.render_text_mixed(txt, 20, (255, 255, 255), s, (10, 10))

    live = "LIVES: 3"
    render(live)  # the still-visible key
    for i in range(7):  # fill the cache to exactly cap (1 live + 7 dynamic = 8)
        render(f"{i}%")
    render(live)  # re-access the live key — LRU marks it most-recently-used
    misses_before = tr.mixed_cache_misses

    render("99%")  # new key at cap → triggers eviction (evict oldest, not wholesale)
    render(live)  # still-visible key must still be cached → a HIT

    # Only "99%" composed; the live key survived eviction. Under wholesale-clear the
    # live render would be a second miss (== misses_before + 2).
    assert tr.mixed_cache_misses == misses_before + 1


# --- render_text_simple surface cache (#1263 — B4) --------------------------


def test_simple_repeated_render_rasterises_only_once():
    tr = _tr()
    s = pygame.Surface((300, 60))
    tr.render_text_simple("Lives: 3", 24, (255, 255, 255), s, (10, 10))
    first = tr.simple_cache_misses
    for _ in range(30):
        tr.render_text_simple("Lives: 3", 24, (255, 255, 255), s, (10, 10))
    assert first == 1
    assert tr.simple_cache_misses == first  # 30 more renders, zero new rasterisations


def test_simple_distinct_key_rerasterises():
    tr = _tr()
    s = pygame.Surface((300, 60))
    tr.render_text_simple("Damage: 0%", 24, (255, 0, 0), s, (10, 10))
    m = tr.simple_cache_misses
    tr.render_text_simple("Damage: 0%", 24, (0, 255, 0), s, (10, 10))  # new colour
    tr.render_text_simple("Damage: 5%", 24, (255, 0, 0), s, (10, 10))  # new text
    assert tr.simple_cache_misses == m + 2


def test_simple_repeat_call_does_not_recall_font_render(monkeypatch):
    """The acceptance guard: a repeat call must NOT re-invoke font.render (#1263)."""
    tr = _tr()

    class _CountingFont:
        def __init__(self, real):
            self._real = real
            self.render_calls = 0

        def render(self, *a, **k):
            self.render_calls += 1
            return self._real.render(*a, **k)

        def __getattr__(self, name):
            return getattr(self._real, name)

    counting = _CountingFont(pygame.font.Font(None, 24))
    monkeypatch.setattr(tr, "_get_font", lambda name, size: counting)
    s = pygame.Surface((300, 60))
    tr.render_text_simple("FPS: 60", 24, (255, 255, 255), s, (10, 10))
    tr.render_text_simple("FPS: 60", 24, (255, 255, 255), s, (10, 10))
    assert counting.render_calls == 1  # rasterised once across two identical calls


def test_simple_cache_lru_keeps_still_visible_key_at_cap():
    """At cap, a still-visible (re-accessed) key survives eviction (#1287).

    Mirrors the #1267 mixed-cache guard onto _simple_surface_cache. The old code
    did a wholesale `clear()` at cap, dropping a live HUD key (Lives / damage /
    pause hint) alongside the cold dynamic churn — the same periodic recompose
    hitch #1267 removed from the mixed cache. LRU eviction (evict oldest, move-to-
    end on access) must keep the still-visible key. Able to fail: under wholesale-
    clear the final live render is a second miss.
    """
    tr = _tr()
    tr._SIMPLE_CACHE_CAP = 8
    s = pygame.Surface((300, 60))

    def render(txt):
        tr.render_text_simple(txt, 24, (255, 255, 255), s, (10, 10))

    live = "Lives: 3"
    render(live)  # the still-visible key
    for i in range(7):  # fill the cache to exactly cap (1 live + 7 dynamic = 8)
        render(f"FPS: {i}")
    render(live)  # re-access the live key — LRU marks it most-recently-used
    misses_before = tr.simple_cache_misses

    render("FPS: 99")  # new key at cap → triggers eviction (evict oldest, not wholesale)
    render(live)  # still-visible key must still be cached → a HIT

    # Only "FPS: 99" composed; the live key survived eviction. Under wholesale-clear
    # the live render would be a second miss (== misses_before + 2).
    assert tr.simple_cache_misses == misses_before + 1


def test_simple_cached_output_is_byte_identical_to_direct_render():
    # ASCII-only strings → fallback_text == text, so the reference is a bare
    # font.render(); proves the cached blit matches an uncached one pixel-for-pixel.
    for txt, center in [("Lives: 3", False), ("Damage: 88%", True), ("P1  WINS", True)]:
        tr = _tr()
        a = pygame.Surface((360, 70))
        a.fill((5, 8, 12))
        b = pygame.Surface((360, 70))
        b.fill((5, 8, 12))
        tr.render_text_simple(txt, 24, (240, 240, 40), a, (180, 30), center=center)
        rendered = tr._get_font(None, 24).render(txt, True, (240, 240, 40))
        if center:
            b.blit(rendered, rendered.get_rect(center=(180, 30)))
        else:
            b.blit(rendered, (180, 30))
        assert pygame.image.tobytes(a, "RGBA") == pygame.image.tobytes(b, "RGBA"), txt
