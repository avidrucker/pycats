"""Implicit "last used" keybinding slot (#1306, ruling C on #1305).

Auto-persisted counterpart of the explicit named schemes (#440): the bindings a
player had when they quit are what they get on next launch. Stored in a dedicated
`profiles/last_keybindings.json` ({"p1": {...}, "p2": {...}}), separate from the
named-scheme store so `list_sets()` never shows it. Same PYCATS_CONFIG_DIR /
PYCATS_NO_PERSIST leaf-entry conventions as settings (#95).
"""

import json

import pygame
import pytest

from pycats.core.keymap import Keymap
from pycats.storage import keybind_store


def _p1():
    return Keymap(dict(attack=pygame.K_v, shield=pygame.K_x, left=pygame.K_a))


def _p2():
    return Keymap(dict(attack=pygame.K_SLASH, shield=pygame.K_COMMA, left=pygame.K_LEFT))


@pytest.fixture(autouse=True)
def _tmp_config(tmp_path, monkeypatch):
    monkeypatch.setenv("PYCATS_CONFIG_DIR", str(tmp_path))
    monkeypatch.delenv("PYCATS_NO_PERSIST", raising=False)


def test_last_used_round_trips_a_rebind_across_a_simulated_restart():
    """The #1302 repro: rebind, quit, relaunch — the change survives. Session 1
    rebinds P1 attack V->K and saves on quit; session 2 boots from factory defaults
    and loads the slot, and the new binding is present rather than the factory V."""
    p1, p2 = _p1(), _p2()
    p1.rebind("attack", pygame.K_k)  # user remaps P1 attack
    keybind_store.save_last_used(p1, p2)  # on quit

    boot_p1, boot_p2 = _p1(), _p2()  # fresh factory keymaps at relaunch
    keybind_store.load_last_used(boot_p1, boot_p2)
    assert boot_p1["attack"] == pygame.K_k  # survived — NOT the factory V
    assert boot_p1["shield"] == pygame.K_x  # untouched action persists
    assert boot_p2["attack"] == pygame.K_SLASH  # the other player round-trips too


def test_last_used_missing_slot_leaves_factory_defaults():
    """No saved slot (first-ever launch) -> both keymaps stay at factory defaults,
    no crash."""
    boot_p1, boot_p2 = _p1(), _p2()
    keybind_store.load_last_used(boot_p1, boot_p2)
    assert dict(boot_p1) == dict(_p1())
    assert dict(boot_p2) == dict(_p2())


def test_last_used_serializes_key_names_not_codes():
    """On-disk values are human-readable key NAMES (like save_set), not raw ints."""
    p1, p2 = _p1(), _p2()
    p1.rebind("attack", pygame.K_k)
    keybind_store.save_last_used(p1, p2)
    with open(keybind_store._last_used_path(), encoding="utf-8") as fh:
        raw = json.load(fh)
    assert raw["p1"]["attack"] == "k"  # a key name, not 107
    assert raw["p2"]["left"] == "left"  # arrow serializes by name


def test_last_used_falls_back_to_factory_for_unparseable_or_missing_entries():
    """A missing action or an unparseable key name in the slot degrades to that
    action's factory default (mirrors load_set)."""
    path = keybind_store._last_used_path()
    import os

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        # p1 has a bad 'left' and no 'shield'; p2 absent entirely
        json.dump({"p1": {"attack": "k", "left": "boguskey"}}, fh)
    boot_p1, boot_p2 = _p1(), _p2()
    keybind_store.load_last_used(boot_p1, boot_p2)
    assert boot_p1["attack"] == pygame.K_k  # from the slot
    assert boot_p1["left"] == pygame.K_a  # unparseable -> factory default
    assert boot_p1["shield"] == pygame.K_x  # missing -> factory default
    assert dict(boot_p2) == dict(_p2())  # absent player -> factory defaults


def test_last_used_corrupt_file_leaves_factory_defaults():
    """A corrupt slot file degrades to factory defaults, no crash."""
    path = keybind_store._last_used_path()
    import os

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("{ not valid json")
    boot_p1, boot_p2 = _p1(), _p2()
    keybind_store.load_last_used(boot_p1, boot_p2)
    assert dict(boot_p1) == dict(_p1())


def test_last_used_is_separate_from_named_schemes():
    """Saving the implicit slot never adds a named scheme (list_sets stays empty)."""
    p1, p2 = _p1(), _p2()
    keybind_store.save_last_used(p1, p2)
    assert keybind_store.list_sets() == []


def test_last_used_persist_disabled_is_a_noop():
    """PYCATS_NO_PERSIST=1 -> save writes nothing and load leaves factory defaults
    (the auto-trigger leaf entry honors the settings kill-switch)."""
    import os

    os.environ["PYCATS_NO_PERSIST"] = "1"
    try:
        p1, p2 = _p1(), _p2()
        p1.rebind("attack", pygame.K_k)
        keybind_store.save_last_used(p1, p2)
        assert not os.path.exists(keybind_store._last_used_path())  # nothing written
        boot_p1, boot_p2 = _p1(), _p2()
        keybind_store.load_last_used(boot_p1, boot_p2)
        assert dict(boot_p1) == dict(_p1())  # load is a no-op -> factory
    finally:
        del os.environ["PYCATS_NO_PERSIST"]
