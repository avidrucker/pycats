# tests/test_player_nickname.py
#
# Player.nickname (#478, slice 1 of #441): a separate display-name field, NOT a
# rename of char_name (which stays the win-attribution identity). Defaults to None
# so the render path falls back to "P1"/"P2" (byte-identical).
import pygame

from pycats.entities.player import Player

P1 = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w, down=pygame.K_s,
          attack=pygame.K_v, special=pygame.K_c, shield=pygame.K_x)


def _mk_player():
    return Player(100, 100, P1, (255, 160, 64), eye_color=(0, 0, 0),
                  char_name="P1", facing_right=True)


def test_nickname_defaults_to_none():
    assert _mk_player().nickname is None


def test_nickname_is_separate_from_char_name():
    p = _mk_player()
    p.nickname = "ACE"
    assert p.nickname == "ACE"
    assert p.char_name == "P1"          # identity is untouched by a display nickname
