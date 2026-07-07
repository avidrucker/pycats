"""Char-select per-player selected-character display row — a fixed row of four
player slots (P1..P4) that each render that player's committed Selection (Character +
Skin), separate from the per-Character selection grid (#682).

P1/P2 slots paint the player's selected Character in their currently-cycled Skin; P3/P4
are inert stubs (4-player support does not exist yet). Distinct from the retired-by-#676
confirmation preview cat (`_confirmation_preview_pos`) and from the grid tiles.
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


def _slot_body(sel, screen, slot_index):
    """RGB at the body centre of the player-slot tile ``slot_index`` (0=P1 .. 3=P4)."""
    x, y, size = sel._player_slot_rect(slot_index)
    return screen.get_at((x + size // 2, y + size // 2))[:3]


def test_p1_slot_shows_selection_in_chosen_skin():
    # nalio's default skin is calico (255,160,64). P1 confirmed on void (20,20,20) — a colour
    # nothing on the slot shares — so the P1 slot's cat must follow the chosen Skin.
    sel = _sel()
    sel.p1_selected = "nalio"
    sel.p1_confirmed = True
    sel.p1_palette = "void"

    screen = pygame.Surface((960, 540))
    sel.render(screen)

    body = _slot_body(sel, screen, 0)
    # Able-to-fail: red if the slot falls back to the archetype default (calico) while a Skin
    # is selected — i.e. `_draw_cat_preview` is called without the player's palette_key.
    assert body == tuple(palette_for("void")["color"]), body
    assert body != tuple(palette_for("nalio")["color"])  # not the archetype default


def test_p2_slot_follows_p2_palette_independently():
    # Per-player: the P2 slot resolves from p2_palette, not P1's or the archetype default.
    sel = _sel()
    sel.p2_selected = "birky"  # default skin ghost
    sel.p2_confirmed = True
    sel.p2_palette = "tiger"

    screen = pygame.Surface((960, 540))
    sel.render(screen)

    body = _slot_body(sel, screen, 1)
    assert body == tuple(palette_for("tiger")["color"]), body
    assert body != tuple(palette_for("birky")["color"])  # not birky's default (ghost)


def test_four_distinct_slots_and_p3_p4_are_stubs():
    sel = _sel()
    rects = [sel._player_slot_rect(i) for i in range(4)]
    xs = [r[0] for r in rects]
    assert len(set(xs)) == 4 and xs == sorted(xs)  # four distinct slots, left-to-right

    # P3 has no player behind it — its slot renders a placeholder, never a live archetype cat.
    screen = pygame.Surface((960, 540))
    sel.render(screen)
    body = _slot_body(sel, screen, 2)
    archetype_bodies = {tuple(palette_for(a)["color"]) for a in sel.characters}
    assert body not in archetype_bodies, body  # a stub, not a rendered cat
