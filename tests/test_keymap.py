"""Per-player rebindable keymap model (#439).

A `Keymap` is a mutable action->keycode map seeded from factory defaults, with
per-player rebinding + reset. Pure (pygame-free — keys are ints), so the whole
model is unit-tested here with no UI. It's a `dict` subclass so it drops into the
existing `self.controls["attack"]` / `.controls.get(name)` reads unchanged.
"""
import pytest

from pycats.core.keymap import Keymap, KeyBindingConflict


_DEFAULTS = {"left": 1, "right": 2, "attack": 3, "shield": 4}


def test_new_keymap_exposes_its_factory_defaults():
    km = Keymap(_DEFAULTS)
    assert km["attack"] == 3
    assert km.get("shield") == 4


def test_get_returns_none_for_an_unbound_action():
    km = Keymap(_DEFAULTS)
    assert km.get("special") is None


def test_rebind_points_the_action_at_the_new_key():
    km = Keymap(_DEFAULTS)
    km.rebind("attack", 9)
    assert km["attack"] == 9   # the action now reads the new key
    assert 3 not in km.values()  # the old key no longer drives any action


def test_rebind_to_a_key_used_by_another_action_raises_and_leaves_map_unchanged():
    km = Keymap(_DEFAULTS)
    with pytest.raises(KeyBindingConflict) as exc:
        km.rebind("attack", 4)     # 4 is already 'shield'
    assert exc.value.action == "shield"   # names the conflicting action for the UI
    assert km["attack"] == 3 and km["shield"] == 4   # map untouched


def test_rebind_an_action_to_its_own_current_key_is_a_noop():
    km = Keymap(_DEFAULTS)
    km.rebind("attack", 3)         # already its key — not a conflict with itself
    assert km["attack"] == 3


def test_reset_restores_the_factory_defaults():
    km = Keymap(_DEFAULTS)
    km.rebind("attack", 9)
    km.rebind("left", 8)
    km.reset()
    assert km == _DEFAULTS


def test_reset_and_rebind_on_one_keymap_do_not_affect_another():
    a = Keymap(_DEFAULTS)
    b = Keymap(_DEFAULTS)
    a.rebind("attack", 9)
    assert b["attack"] == 3        # b's map is its own
    a.reset()
    assert a["attack"] == 3 and b["attack"] == 3


def test_a_player_reads_a_rebound_keymap_and_not_the_old_key():
    # Integration contract: a Keymap is a drop-in for the plain `controls` dict, so a
    # rebind on it is seen live by the Player that reads `self.controls`.
    import pygame
    from pycats.sim.runner import build_players, P1_KEYS
    p1, _p2, _group = build_players()
    p1.controls = Keymap(dict(P1_KEYS))
    old, new = P1_KEYS["attack"], pygame.K_j
    assert p1._pressed({old}, "attack")          # old key drives attack
    p1.controls.rebind("attack", new)
    assert p1._pressed({new}, "attack")          # rebound key now drives it
    assert not p1._pressed({old}, "attack")      # old key no longer does
