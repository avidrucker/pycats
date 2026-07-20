"""Char-select skin rendering — the **Character Roster Tile** stays at the Character's
default Skin; a player's cycled Skin shows only in their **Player Choice Slot** (#761).

#676 made the roster tile itself recolor to the confirmed player's cycled Skin. #761
reverses that: two players can pick the same Character and each cycle their own Skin, so a
shared roster tile must NOT try to represent either player's Skin — it always paints the
Character default. Player presence on a tile is the P1-red / P2-blue selection outline
(nested when both share a Character); the cycled Skin lives only in the Player Choice Slot
(#682, tested in test_char_select_player_slots.py). Vocabulary: #673.
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

from pycats.char_select import CharacterSelector  # noqa: E402
from pycats.characters.roster import palette_for  # noqa: E402
from pycats.config import CHAR_SELECT_TILE_SIZE  # noqa: E402

_P1 = {"left": 1, "right": 2, "up": 3, "down": 4, "attack": 5, "special": 6}
_P2 = {"left": 11, "right": 12, "up": 13, "down": 14, "attack": 15, "special": 16}


def _sel():
    pygame.init()
    return CharacterSelector(_P1, _P2)


def _confirm_p1(sel, char_index=0):
    sel.p1_cursor = char_index
    sel.p1_input_cooldown = 0
    sel.update(set(), {_P1["attack"]})


def _confirm_p2(sel, char_index=0):
    sel.p2_cursor = char_index
    sel.p2_input_cooldown = 0
    sel.update(set(), {_P2["attack"]})


def _cycle_p1(sel, direction="right"):
    sel.p1_input_cooldown = 0
    sel.update(set(), {_P1[direction]})


def _cycle_p1_to(sel, skin_key):
    for _ in range(20):
        if sel.p1_palette == skin_key:
            return
        _cycle_p1(sel, "right")
    raise AssertionError(f"never cycled to {skin_key}; stuck at {sel.p1_palette}")


def _color(skin_key):
    return tuple(palette_for(skin_key)["color"])


def _tile_body(sel, screen, char_pos):
    """RGB at the body centre of the roster tile at ``char_pos``."""
    x, y = sel._grid_pos_to_screen_pos(char_pos)
    return screen.get_at((x + CHAR_SELECT_TILE_SIZE // 2, y + CHAR_SELECT_TILE_SIZE // 2))[:3]


def test_roster_tile_keeps_default_skin_after_a_player_cycles():
    # THE #761 regression: P1 confirms nalio and cycles to void (20,20,20). Nalio's ROSTER
    # TILE must stay its default (red-blue), NOT repaint in P1's cycled Skin. Able-to-fail:
    # red on the #676 code that painted the tile from `_active_skin_by_char`.
    sel = _sel()
    _confirm_p1(sel, 0)  # nalio
    _cycle_p1_to(sel, "void")

    screen = pygame.Surface((960, 540))
    sel.render(screen)

    char_pos = sel.characters.index("nalio")
    body = _tile_body(sel, screen, char_pos)
    assert body == _color("nalio"), body  # stays the Character default
    assert body != _color("void")  # NOT the player's cycled Skin


def test_unconfirmed_tile_keeps_the_character_default_skin():
    # A tile no player has confirmed shows the Character's own default palette, unchanged.
    sel = _sel()
    screen = pygame.Surface((960, 540))
    sel.render(screen)
    char_pos = sel.characters.index("narz")
    assert _tile_body(sel, screen, char_pos) == _color("narz")


def test_tile_skin_cache_and_helpers_are_gone():
    # #761 removed the per-Character tile-skin cache and its two helpers — their sole reader
    # was the tile paint, now removed. Able-to-fail: red if any is reintroduced.
    sel = _sel()
    assert not hasattr(sel, "_active_skin_by_char")
    assert not hasattr(sel, "_tile_owner_skin")
    assert not hasattr(sel, "_release_tile")


def test_external_preview_cat_is_retired():
    # #676: the separate recolored preview cat drawn outside the grid is gone (still true).
    sel = _sel()
    assert not hasattr(sel, "_confirmation_preview_pos")


def test_no_skin_readout_under_the_roster_tile(monkeypatch):
    # #761 deliverable 2: the `P1 ✓ {skin}` readout is dropped from the roster tile — the
    # skin NAME belongs only to the Player Choice Slot. Able-to-fail: red on #676's code,
    # which renders "P1 ✓ Void" in the grid band under the tile.
    from pycats import text_utils

    sel = _sel()
    _confirm_p1(sel, 0)  # nalio
    _cycle_p1_to(sel, "void")

    calls = []  # (text, pos)
    orig = text_utils.render_text

    def spy(screen, text, pos, *a, **k):
        calls.append((str(text), pos))
        return orig(screen, text, pos, *a, **k)

    monkeypatch.setattr(text_utils, "render_text", spy)

    orig_mixed = text_utils.text_renderer.render_text_mixed

    def spy_mixed(text, size, color, screen, pos, *a, **k):
        calls.append((str(text), pos))
        return orig_mixed(text, size, color, screen, pos, *a, **k)

    monkeypatch.setattr(text_utils.text_renderer, "render_text_mixed", spy_mixed)

    screen = pygame.Surface((960, 540))
    sel.render(screen)

    x, y = sel._grid_pos_to_screen_pos(0)
    skin_name = palette_for("void")["name"].lower()  # "void"
    # The grid band spans from just above the tile to below where #676 drew its skin label;
    # the Player Choice Slot row sits well below this band.
    band = range(y - 20, y + CHAR_SELECT_TILE_SIZE + 40)
    leaked = [(t, p) for (t, p) in calls if skin_name in t.lower() and p[1] in band]
    assert leaked == [], f"skin name leaked onto the roster tile: {leaked}"


def test_sole_occupant_outline_is_normal_geometry():
    # One player alone on a Character → normal outline, no nesting.
    sel = _sel()
    _confirm_p1(sel, 0)  # nalio, alone
    assert sel._confirm_rank(1) is None
    normal = sel._confirm_outline_rect(0, None)
    assert sel._confirm_outline_rect(0, sel._confirm_rank(1)) == normal


def test_shared_character_nests_outlines_first_inner_second_outer():
    # Both players confirm nalio. The FIRST confirmer (P1) nests INNER (smaller rect); the
    # SECOND (P2) nests OUTER (bigger rect). Able-to-fail: red if both draw the same rect
    # (no nesting) or the order is reversed.
    sel = _sel()
    _confirm_p1(sel, 0)  # nalio first
    _confirm_p2(sel, 0)  # nalio second

    assert sel._confirm_rank(1) == "inner"
    assert sel._confirm_rank(2) == "outer"

    inner = sel._confirm_outline_rect(0, "inner")
    normal = sel._confirm_outline_rect(0, None)
    outer = sel._confirm_outline_rect(0, "outer")
    # strictly nested: inner ⊂ normal ⊂ outer
    assert inner.width < normal.width < outer.width
    assert inner.height < normal.height < outer.height
    assert normal.contains(inner) and outer.contains(normal)


def test_cancel_clears_confirm_order_so_nesting_reverts():
    # P1 then P2 confirm nalio (P1 inner, P2 outer). P1 cancels; P2 is now alone → normal.
    sel = _sel()
    _confirm_p1(sel, 0)
    _confirm_p2(sel, 0)
    sel.p1_input_cooldown = 0
    sel.update(set(), {_P1["special"]})  # P1 cancels
    assert sel.p1_confirm_seq is None
    assert sel._confirm_rank(2) is None  # P2 alone → normal geometry
