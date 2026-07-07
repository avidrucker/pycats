"""Char-select live skin preview — the confirmed player's preview cat recolors to the
cycled OG skin, per-player (#662, follow-up to #650).

#650 only surfaced the chosen skin as a small swatch; the preview cat kept the archetype
default palette. #662 recolors an actual per-player preview cat via `_draw_cat_preview`'s
`palette_key` override, drawn side-by-side so two players who picked the SAME character each
see their own skin (the case #650 deferred).
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

from pycats.char_select import CharacterSelector  # noqa: E402
from pycats.characters.roster import palette_for  # noqa: E402

_P1 = {"left": 1, "right": 2, "up": 3, "down": 4, "attack": 5, "special": 6}
_P2 = {"left": 11, "right": 12, "up": 13, "down": 14, "attack": 15, "special": 16}


def _sel():
    pygame.init()
    return CharacterSelector(_P1, _P2)


def _sample(sel, screen, char_pos, is_p1):
    """RGB at the body centre of a confirmed player's recolored preview cat."""
    px, py, size = sel._confirmation_preview_pos(char_pos, is_p1)
    return screen.get_at((px + size // 2, py + size // 2))[:3]


def test_confirmed_preview_cat_recolors_to_the_cycled_skin():
    # nalio's default skin is calico (255,160,64). Cycle P1 to void (20,20,20) — a colour
    # nothing else on the tile shares — and the preview cat body must follow the chosen skin.
    sel = _sel()
    sel.p1_selected = "nalio"
    sel.p1_confirmed = True
    sel.p1_palette = "void"

    screen = pygame.Surface((960, 540))
    sel.render(screen)

    char_pos = sel.characters.index("nalio")
    body = _sample(sel, screen, char_pos, is_p1=True)
    # Able-to-fail: red if the preview falls back to the archetype default (calico) while a
    # skin is selected — i.e. `_draw_cat_preview` is called without the player's palette_key.
    assert body == tuple(palette_for("void")["color"]), body
    assert body != tuple(palette_for("nalio")["color"])  # not the archetype default


def test_two_players_same_character_each_keep_their_own_skin():
    # Both pick nalio; P1 -> void (20,20,20), P2 -> ghost (255,255,255). The two previews
    # sit at distinct positions and each shows its own skin — no shared-tile conflict.
    sel = _sel()
    sel.p1_selected = sel.p2_selected = "nalio"
    sel.p1_confirmed = sel.p2_confirmed = True
    sel.p1_palette, sel.p2_palette = "void", "ghost"

    screen = pygame.Surface((960, 540))
    sel.render(screen)

    char_pos = sel.characters.index("nalio")
    p1_pos = sel._confirmation_preview_pos(char_pos, True)
    p2_pos = sel._confirmation_preview_pos(char_pos, False)
    assert p1_pos[:2] != p2_pos[:2]  # separate previews, not one overlapping cat

    assert _sample(sel, screen, char_pos, is_p1=True) == tuple(palette_for("void")["color"])
    assert _sample(sel, screen, char_pos, is_p1=False) == tuple(palette_for("ghost")["color"])
