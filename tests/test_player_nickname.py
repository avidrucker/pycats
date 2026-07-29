# tests/test_player_nickname.py
#
# Player.nickname (#478, slice 1 of #441): a separate display-name field, NOT a
# rename of char_name (which stays the win-attribution identity). Defaults to None
# so the render path falls back to "P1"/"P2" (byte-identical).
from helpers import mk_player as _mk_player


def test_nickname_defaults_to_none():
    assert _mk_player().nickname is None


def test_nickname_is_separate_from_char_name():
    p = _mk_player()
    p.nickname = "ACE"
    assert p.nickname == "ACE"
    assert p.char_name == "P1"          # identity is untouched by a display nickname
