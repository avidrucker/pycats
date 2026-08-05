"""
Tests for the JSON branch of load_fighter_data (#844, R4 of the #792 editor;
design docs/pycats-editor-data-schema-design.md §2.1 + §2.2).

R4 wires the R3 hydrate (_fighter_from_json) into load_fighter_data: when
`CHARACTER_DATA_DIR / f"{character}.json"` exists it is hydrated and returned.
The four archetypes + default all ship JSON, and since #1141 the mirror is the
sole source (the Python oracles are retired): a JSON-less archetype now raises
rather than flooring to a Python literal. These tests monkeypatch
CHARACTER_DATA_DIR to a tmp dir to exercise the branch in isolation.
"""

import json

import pytest

from pycats.combat.data import (
    FighterData,
    _fighter_from_json,
    load_fighter_data,
)


def _jab_doc(character="testjson"):
    """Minimal thin-mirror document (the R3 jab fixture) for a made-up key."""
    return {
        "schema_version": 1,
        "character": character,
        "weight": 100,
        "hurtbox": {"circles": [[20, 15, 14], [20, 45, 14]]},
        "moves": {
            "jab": {
                "name": "jab",
                "in_air": False,
                "startup": 1,
                "active": 2,
                "recovery": 13,
                "hitboxes": [
                    {
                        "circle": [54, 27, 19],
                        "damage": 3.0,
                        "angle": 83,
                        "knockback_growth": 100.0,
                        "set_knockback": 20,
                    },
                ],
            }
        },
    }


def _write_json(dir_path, character, doc):
    path = dir_path / f"{character}.json"
    path.write_text(json.dumps(doc))
    return path


# --- Branch fires when a <character>.json exists (able-to-fail) ---------------


def test_json_branch_loads_hydrated_fighter(tmp_path, monkeypatch):
    monkeypatch.setattr("pycats.combat.data.CHARACTER_DATA_DIR", tmp_path)
    doc = _jab_doc("testjson")
    _write_json(tmp_path, "testjson", doc)
    fd = load_fighter_data("testjson")
    assert isinstance(fd, FighterData)
    assert fd == _fighter_from_json(doc)  # branch returned the hydrated data


# --- Retired Python fallback: a JSON-less archetype now raises (#1141) --------


def test_no_json_archetype_now_raises(tmp_path, monkeypatch):
    # #1141 retired the Python-literal fallback arms: with no <archetype>.json the
    # loader no longer floors to a Python literal — a known archetype key whose
    # JSON is absent is a loud failure, exactly like an unknown key. Able-to-fail:
    # restore an arm and this returns a fighter instead of raising.
    monkeypatch.setattr("pycats.combat.data.CHARACTER_DATA_DIR", tmp_path)  # empty dir
    from pycats.combat.errors import UnknownCharacter

    with pytest.raises(UnknownCharacter):
        load_fighter_data("nalio")


def test_unknown_key_raises(tmp_path, monkeypatch):
    # Since #887/#881 an unknown key is a programming error and raises loudly — it
    # no longer resolves to the default. The raise fires on the allow-list check
    # (no <key>.json, not an archetype, not an intended-default key), so it does
    # not depend on default.json being present in the monkeypatched dir.
    monkeypatch.setattr("pycats.combat.data.CHARACTER_DATA_DIR", tmp_path)
    from pycats.combat.errors import UnknownCharacter

    with pytest.raises(UnknownCharacter):
        load_fighter_data("no_such_cat")


# --- The JSON branch fires for a real archetype key, not just made-up keys ----


def test_json_branch_fires_for_a_real_archetype_key(tmp_path, monkeypatch):
    monkeypatch.setattr("pycats.combat.data.CHARACTER_DATA_DIR", tmp_path)
    # A nalio.json with a distinguishable weight — the branch resolves a real
    # archetype key straight from its file (the sole source since #1141).
    doc = _jab_doc("nalio")
    doc["weight"] = 123
    _write_json(tmp_path, "nalio", doc)
    fd = load_fighter_data("nalio")
    assert fd.weight == 123  # came from nalio.json


# --- Golden-safety: no committed <character>.json ships in the repo -----------


def test_shipped_json_files_hydrate_cleanly():
    """Every committed <character>.json must be a valid, current-schema thin
    mirror that hydrates without error.

    Fighters are flipped onto JSON one-at-a-time (#851 flipped Nalio first); this
    guard scales to each new file with no edit. Per-fighter byte-equality to the
    Python oracle — the golden-safety proof — lives in that fighter's own flip
    test (e.g. tests/test_nalio_json_flip.py), not here."""
    from pycats.combat.data import CHARACTER_DATA_DIR, SCHEMA_VERSION, fighter_json_paths

    if not CHARACTER_DATA_DIR.exists():
        return
    for path in fighter_json_paths():
        doc = json.loads(path.read_text())
        assert doc.get("schema_version") == SCHEMA_VERSION, f"{path.name}: wrong/absent schema_version"
        _fighter_from_json(doc)  # raises if malformed / off-schema
