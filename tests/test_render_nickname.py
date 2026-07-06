"""draw_player_name nickname + slot-colour seam (#478).

The label above a fighter shows `nickname or char_name`; its colour is selected by
the player *slot* (char_name — the P1/P2 identity), NOT by the displayed text. A
None nickname renders "P1"/"P2" exactly as before (byte-identical → the render-parity
oracle stays green). Pixel-level (pygame.image.tobytes) comparisons, headless.
"""


import pygame

from pycats import render_battle
from pycats.config import SCREEN_HEIGHT, SCREEN_WIDTH


class _FakeP:
    """The minimal surface draw_player_name reads: a rect + char_name + nickname."""
    def __init__(self, char_name, nickname=None):
        self.rect = pygame.Rect(200, 200, 40, 60)
        self.char_name = char_name
        self.nickname = nickname


def _render(p):
    pygame.init()
    surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    render_battle.draw_player_name(surf, p)
    return pygame.image.tobytes(surf, "RGB")


def test_nickname_is_used_as_the_label_when_set():
    assert _render(_FakeP("P1")) != _render(_FakeP("P1", "ACE"))    # nickname changes the label


def test_none_nickname_falls_back_to_char_name_text():
    assert _render(_FakeP("P1", None)) == _render(_FakeP("P1", "P1"))   # None -> char_name text


def test_label_colour_follows_the_slot_not_the_display_text():
    # Same display text, different slot -> different accent colour -> different pixels.
    assert _render(_FakeP("P1", "SAME")) != _render(_FakeP("P2", "SAME"))


def test_body_composite_reflects_and_invalidates_on_nickname():
    # The label is drawn through the cached body composite (via _CatShim); a nickname
    # change must reach the label AND bust the cache (nickname in the cache key).
    from pycats.entities.player import Player
    keys = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w, down=pygame.K_s,
                attack=pygame.K_v, special=pygame.K_c, shield=pygame.K_x)
    p = Player(200, 200, keys, (255, 160, 64), eye_color=(0, 0, 0), char_name="P1")
    before = pygame.image.tobytes(render_battle._cat_body_surface(p), "RGB")
    p.nickname = "ACE"
    after = pygame.image.tobytes(render_battle._cat_body_surface(p), "RGB")
    assert before != after
