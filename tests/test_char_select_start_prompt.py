"""Start prompt (#663) — de-modalize the "both confirmed" state.

#650 added live skin cycling after a player confirms, but the moment BOTH players
confirm, `show_start_screen` flips and `update` used to early-return after only handling
B — so cycling stopped and a full-screen dim + modal box (`_draw_start_overlay`) covered
the grid. #663 replaces that modal with a non-obscuring message strip BELOW the grid and
keeps left/right cycling live in the start-prompt state. A still starts, B still goes back.
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

from pycats.char_select import GRID_START_Y, PLAYER_SLOT_ROW_Y, CharacterSelector  # noqa: E402
from pycats.config import CHAR_SELECT_TILE_SIZE, SCREEN_HEIGHT, SCREEN_WIDTH  # noqa: E402

_P1 = {"left": 1, "right": 2, "up": 3, "down": 4, "attack": 5, "special": 6}
_P2 = {"left": 11, "right": 12, "up": 13, "down": 14, "attack": 15, "special": 16}


def _sel():
    pygame.init()
    return CharacterSelector(_P1, _P2)


def _both_confirm(sel, p1_char=0, p2_char=1):
    """Confirm P1 on p1_char and P2 on p2_char (distinct Characters → no FCFS lock),
    landing in the start-prompt state (show_start_screen True, delay elapsed)."""
    sel.p1_cursor = p1_char
    sel.p2_cursor = p2_char
    sel.p1_input_cooldown = 0
    sel.p2_input_cooldown = 0
    sel.update(set(), {_P1["attack"], _P2["attack"]})
    # one more tick to flip show_start_screen and burn down the input delay
    for _ in range(10):
        sel.p1_input_cooldown = 0
        sel.p2_input_cooldown = 0
        sel.update(set(), set())
    assert sel.show_start_screen is True


def test_skin_cycling_still_works_after_both_confirm():
    # THE #663 able-to-fail test: in the start-prompt state, a left/right press still
    # advances that player's palette. Red today — update early-returns in the
    # show_start_screen branch, so the palette never changes.
    sel = _sel()
    _both_confirm(sel)
    before = sel.p1_palette
    sel.p1_input_cooldown = 0
    sel.update(set(), {_P1["right"]})
    assert sel.p1_palette != before, "left/right must still cycle P1's skin in the start prompt"

    # and P2 independently
    before2 = sel.p2_palette
    sel.p2_input_cooldown = 0
    sel.update(set(), {_P2["left"]})
    assert sel.p2_palette != before2, "left/right must still cycle P2's skin in the start prompt"


def test_a_still_starts_the_match_from_the_prompt():
    sel = _sel()
    _both_confirm(sel)
    sel.p1_input_cooldown = 0
    assert sel.ready_to_start({_P1["attack"]}) is True


def test_b_still_unconfirms_and_leaves_the_prompt():
    sel = _sel()
    _both_confirm(sel)
    sel.p1_input_cooldown = 0
    sel.update(set(), {_P1["special"]})
    assert sel.show_start_screen is False
    assert sel.p1_confirmed is False
    assert sel.p2_confirmed is True  # only the player who pressed B backs out


def test_no_full_screen_dim_over_the_grid_when_both_confirm():
    # The modal dimmed every pixel. #663: the grid tile body must render identically
    # whether or not the start prompt is showing (no full-screen dim covering it).
    sel = _sel()
    sel.p1_cursor = 0
    sel.p2_cursor = 1
    sel.p1_input_cooldown = 0
    sel.p2_input_cooldown = 0
    sel.update(set(), {_P1["attack"], _P2["attack"]})

    x, y = sel._grid_pos_to_screen_pos(2)  # an unconfirmed tile (no outline over it)
    probe = (x + CHAR_SELECT_TILE_SIZE // 2, y + CHAR_SELECT_TILE_SIZE // 2)

    sel.show_start_screen = False
    plain = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    sel.render(plain)
    undimmed = plain.get_at(probe)[:3]

    sel.show_start_screen = True
    prompt = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    sel.render(prompt)
    with_prompt = prompt.get_at(probe)[:3]

    assert with_prompt == undimmed, "the start prompt must not dim/obscure the grid tiles"


def test_modal_overlay_helper_is_gone():
    sel = _sel()
    assert not hasattr(sel, "_draw_start_overlay"), "the modal overlay helper should be removed (#663)"


def test_start_prompt_text_renders_below_the_grid():
    # Same text the modal carried, now drawn in the band below the grid (below the last
    # tile row, above the Player Choice Slot row). Red today: the modal centres "START"
    # near the vertical middle of the screen, above the grid's bottom.
    import pycats.char_select as cs

    calls = []
    orig = cs.text_utils.render_text

    def spy(screen, text, pos, *a, **k):
        calls.append((text, pos))
        return orig(screen, text, pos, *a, **k)

    sel = _sel()
    _both_confirm(sel)
    cs.text_utils.render_text = spy
    try:
        screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        sel.render(screen)
    finally:
        cs.text_utils.render_text = orig

    wanted = {"START", "Press A to start the match", "Press B to go back"}
    grid_bottom = GRID_START_Y + CHAR_SELECT_TILE_SIZE  # below the first tile row at least
    for text, pos in calls:
        if text in wanted:
            wanted.discard(text)
            assert grid_bottom < pos[1] < PLAYER_SLOT_ROW_Y, (
                f"start-prompt text {text!r} must render below the grid and above the player slots; got y={pos[1]}"
            )
    assert not wanted, f"start prompt is missing text: {wanted}"
