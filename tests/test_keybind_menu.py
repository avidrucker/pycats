"""Keybinding capture-flow controller (#447).

The testable logic behind the Options keybinding screen: which player/action is
focused, the "press a key to bind" capture flow, conflict handling, and reset —
all pure (the pygame KEYDOWN read + rendering are a thin layer over this).
"""
import pytest

from pycats.core.keymap import Keymap
from pycats.keybind_menu import KeybindMenu


_DEF1 = {"left": 1, "right": 2, "attack": 5, "shield": 7}
_DEF2 = {"left": 11, "right": 12, "attack": 15, "shield": 17}


def _menu():
    return KeybindMenu(Keymap(dict(_DEF1)), Keymap(dict(_DEF2)))


def test_capture_key_rebinds_the_focused_action():
    m = _menu()
    m.focus(0, "attack")
    m.begin_capture()
    assert m.capturing
    ok = m.capture_key(99)
    assert ok is True
    assert not m.capturing            # capture ends on a successful bind
    assert m.binding(0, "attack") == 99


def test_capture_key_conflict_does_not_apply_and_reports_the_clash():
    m = _menu()
    m.focus(0, "attack")
    m.begin_capture()
    ok = m.capture_key(7)             # 7 is already P1's 'shield'
    assert ok is False
    assert not m.capturing            # capture still ends
    assert m.binding(0, "attack") == 5   # binding untouched
    assert "shield" in m.message      # the conflict names the clashing action


def test_reset_player_restores_that_players_defaults_only():
    m = _menu()
    m.focus(0, "attack"); m.begin_capture(); m.capture_key(99)   # P1 attack -> 99
    m.focus(1, "shield"); m.begin_capture(); m.capture_key(99)   # P2 shield -> 99
    m.reset_player(0)
    assert m.binding(0, "attack") == 5    # P1 restored to factory
    assert m.binding(1, "shield") == 99   # P2 untouched


def test_cancel_capture_exits_without_binding():
    m = _menu()
    m.focus(0, "attack")
    m.begin_capture()
    m.cancel_capture()
    assert not m.capturing
    assert m.binding(0, "attack") == 5    # nothing bound
