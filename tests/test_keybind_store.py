"""Keybinding-set persistence (#440): save / name / list / load / delete named keymaps.

Pure JSON store under PYCATS_CONFIG_DIR (pointed at tmp_path here, the #95 pattern).
Bindings serialize as key NAMES, and loading replaces a Keymap wholesale.
"""
import json
import os

import pygame
import pytest

from pycats import keybind_store
from pycats.core.keymap import Keymap


def _km():
    return Keymap(dict(attack=pygame.K_v, shield=pygame.K_x, left=pygame.K_a))


@pytest.fixture(autouse=True)
def _tmp_config(tmp_path, monkeypatch):
    monkeypatch.setenv("PYCATS_CONFIG_DIR", str(tmp_path))


def test_save_set_then_list_sets_returns_the_name():
    keybind_store.save_set("mine", _km())
    assert keybind_store.list_sets() == ["mine"]


def test_round_trip_restores_the_exact_keymap():
    km = _km()                        # attack=V, shield=X, left=A
    keybind_store.save_set("s", km)
    fresh = Keymap(dict(attack=pygame.K_1, shield=pygame.K_2, left=pygame.K_3))
    loaded = keybind_store.load_set("s", fresh)
    assert dict(loaded) == dict(km)   # a file round-trip through JSON restores it exactly
    assert loaded is fresh            # applied in place


def test_format_serializes_key_names_not_codes():
    keybind_store.save_set("s", _km())
    with open(keybind_store._store_path(), encoding="utf-8") as fh:
        raw = json.load(fh)
    assert raw["s"]["attack"] == "v"        # a key NAME, not 118


def test_named_sets_coexist_delete_and_overwrite():
    keybind_store.save_set("a", _km())
    keybind_store.save_set("b", _km())
    assert keybind_store.list_sets() == ["a", "b"]
    keybind_store.delete_set("a")
    assert keybind_store.list_sets() == ["b"]           # delete leaves the other
    keybind_store.save_set("b", Keymap(dict(attack=pygame.K_k, shield=pygame.K_x, left=pygame.K_a)))
    fresh = Keymap(dict(attack=pygame.K_1, shield=pygame.K_2, left=pygame.K_3))
    assert keybind_store.load_set("b", fresh)["attack"] == pygame.K_k   # re-save overwrote


def test_missing_file_lists_no_sets():
    assert keybind_store.list_sets() == []             # nothing saved -> no file, no crash


def test_corrupt_file_degrades_to_no_sets():
    path = keybind_store._store_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("{ not valid json")
    assert keybind_store.list_sets() == []             # no crash


def test_unknown_action_or_unparseable_name_falls_back_to_factory_default():
    path = keybind_store._store_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"s": {"attack": "v", "left": "boguskey"}}, fh)   # no 'shield'; bad 'left'
    loaded = keybind_store.load_set("s", _km())        # factory: attack=V, shield=X, left=A
    assert loaded["attack"] == pygame.K_v              # from the set
    assert loaded["shield"] == pygame.K_x              # missing action -> factory default
    assert loaded["left"] == pygame.K_a                # unparseable name -> factory default


def test_wholesale_replace_allows_a_key_swap_without_conflict():
    swapped = Keymap(dict(attack=pygame.K_x, shield=pygame.K_v))   # attack<->shield vs. below
    keybind_store.save_set("swap", swapped)
    fresh = Keymap(dict(attack=pygame.K_v, shield=pygame.K_x))
    loaded = keybind_store.load_set("swap", fresh)     # sequential rebind would conflict here
    assert loaded["attack"] == pygame.K_x and loaded["shield"] == pygame.K_v
