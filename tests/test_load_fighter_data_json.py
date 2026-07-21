"""
Tests for the JSON branch of load_fighter_data (#844, R4 of the #792 editor;
design docs/pycats-editor-data-schema-design.md §2.1 + §2.2).

R4 wires the R3 hydrate (_fighter_from_json) into load_fighter_data: when
`CHARACTER_DATA_DIR / f"{character}.json"` exists it is hydrated and returned;
otherwise the existing Python import switch runs unchanged. No `<character>.json`
ships in the repo, so the branch never fires for a real character and goldens are
untouched. Tests monkeypatch CHARACTER_DATA_DIR to a tmp dir to exercise the
branch without touching the repo.
"""

import json

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


# --- Fall-through to the Python import switch when no JSON file ---------------


def test_no_json_falls_through_to_python(tmp_path, monkeypatch):
    monkeypatch.setattr("pycats.combat.data.CHARACTER_DATA_DIR", tmp_path)  # empty dir
    fd = load_fighter_data("nalio")
    # identical to the Python-defined Nalio (no JSON present)
    from pycats.characters.nalio_cat import NALIO_FIGHTER_DATA

    assert fd is NALIO_FIGHTER_DATA


def test_unknown_key_still_defaults(tmp_path, monkeypatch):
    monkeypatch.setattr("pycats.combat.data.CHARACTER_DATA_DIR", tmp_path)
    fd = load_fighter_data("no_such_cat")
    from pycats.characters.default_cat import DEFAULT_FIGHTER_DATA

    assert fd is DEFAULT_FIGHTER_DATA


# --- JSON precedence: a <character>.json wins over the Python definition ------


def test_json_takes_precedence_over_python(tmp_path, monkeypatch):
    monkeypatch.setattr("pycats.combat.data.CHARACTER_DATA_DIR", tmp_path)
    # A nalio.json with a distinguishable weight — proves the branch runs BEFORE
    # the `character == "nalio"` Python import.
    doc = _jab_doc("nalio")
    doc["weight"] = 123
    _write_json(tmp_path, "nalio", doc)
    fd = load_fighter_data("nalio")
    assert fd.weight == 123  # came from JSON, not the Python NALIO (weight 100)
    from pycats.characters.nalio_cat import NALIO_FIGHTER_DATA

    assert fd is not NALIO_FIGHTER_DATA


# --- Golden-safety: no committed <character>.json ships in the repo -----------


def test_no_json_files_ship_in_repo():
    """The real CHARACTER_DATA_DIR must contain no *.json (R4 ships the reader
    only; R5 does the migration). Any committed file here would divert a real
    character off its Python definition and could move goldens."""
    from pycats.combat.data import CHARACTER_DATA_DIR

    if CHARACTER_DATA_DIR.exists():
        assert list(CHARACTER_DATA_DIR.glob("*.json")) == []
