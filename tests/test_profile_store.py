"""Player-profile persistence (#478, slice 1 of #441): save / load / list / delete
named player profiles.

A profile is `{ "keybinding_set": name|null, "stats": {} }` — keybindings are
referenced by the NAME of a saved set (#440's keybind_store), not inlined; `stats`
is reserved empty for #442. Pure JSON store under PYCATS_CONFIG_DIR (pointed at
tmp_path here, the #95 pattern), mirroring keybind_store (#440): missing/corrupt
files degrade gracefully, never crash.
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import json

import pytest

from pycats import profile_store


@pytest.fixture(autouse=True)
def _tmp_config(tmp_path, monkeypatch):
    monkeypatch.setenv("PYCATS_CONFIG_DIR", str(tmp_path))


def _profile(keyset=None):
    return {"keybinding_set": keyset, "stats": {}}


def test_save_then_load_round_trips():
    profile_store.save_profile("ACE", _profile("wasd"))
    assert profile_store.load_profile("ACE") == _profile("wasd")


def test_list_profiles_returns_names_sorted():
    profile_store.save_profile("ZED", _profile())
    profile_store.save_profile("ACE", _profile())
    assert profile_store.list_profiles() == ["ACE", "ZED"]


def test_delete_removes_only_that_profile():
    profile_store.save_profile("ACE", _profile())
    profile_store.save_profile("BEA", _profile())
    profile_store.delete_profile("ACE")
    assert profile_store.list_profiles() == ["BEA"]


def test_save_overwrites_an_existing_name():
    profile_store.save_profile("ACE", _profile("wasd"))
    profile_store.save_profile("ACE", _profile("arrows"))
    assert profile_store.load_profile("ACE")["keybinding_set"] == "arrows"


def test_load_missing_profile_returns_none():
    assert profile_store.load_profile("nobody") is None


def test_missing_file_lists_no_profiles():
    assert profile_store.list_profiles() == []          # no file, no crash


def test_corrupt_file_degrades_to_empty():
    path = profile_store._store_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("{ not valid json")
    assert profile_store.list_profiles() == []          # no crash
    assert profile_store.load_profile("ACE") is None


def test_keybinding_set_is_referenced_by_name_not_inlined():
    profile_store.save_profile("ACE", _profile("wasd"))
    with open(profile_store._store_path(), encoding="utf-8") as fh:
        raw = json.load(fh)
    assert raw["ACE"]["keybinding_set"] == "wasd"        # a NAME, not a bindings dict
    assert raw["ACE"]["stats"] == {}                     # reserved empty for #442
