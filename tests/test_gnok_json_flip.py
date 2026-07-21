"""
tests/test_gnok_json_flip.py

Fourth fighter flip (#860, child of #792 editor): Gnok now ships as
`pycats/characters/data/gnok.json` and `load_fighter_data("gnok")` resolves it
through the R4 JSON branch (#844) instead of the Python switch. Mirrors the Nalio
(#851), Birky (#856), and Narz (#858) flips.

The Python literal (`gnok_cat.py` GNOK_FIGHTER_DATA) is retained as the round-trip
ORACLE and fallback (Risk 1 mitigation, ruling on #847). These tests prove the
on-disk file hydrates back byte-equal to that oracle — the guarantee that keeps
the flip golden-safe. Corrupting a value in the committed JSON breaks the
equality below.
"""

import json

from pycats.characters.gnok_cat import GNOK_FIGHTER_DATA
from pycats.combat.data import (
    CHARACTER_DATA_DIR,
    _fighter_to_json,
    load_fighter_data,
)

GNOK_JSON = CHARACTER_DATA_DIR / "gnok.json"


def test_gnok_json_file_ships():
    assert GNOK_JSON.exists(), "the Gnok flip must commit pycats/characters/data/gnok.json"


def test_gnok_loads_from_json_equals_python_oracle():
    # load_fighter_data("gnok") now hits the JSON branch (the file exists), so
    # this asserts the on-disk file hydrates to the exact Python data. Able-to-fail:
    # a wrong value in gnok.json makes the hydrated FighterData != the oracle.
    assert load_fighter_data("gnok") == GNOK_FIGHTER_DATA


def test_committed_json_matches_serializer():
    # Guards against a stale / hand-edited file: the committed bytes must parse to
    # exactly what the R5 serializer emits for the current Python literal.
    on_disk = json.loads(GNOK_JSON.read_text())
    assert on_disk == _fighter_to_json(GNOK_FIGHTER_DATA, "gnok")


def test_migrated_json_has_no_provenance():
    # Migrated data starts with no per-frame trace (§2.4); the editor seeds
    # provenance on first open. The drift-guard (R7) skips moves that lack it.
    assert "provenance" not in json.loads(GNOK_JSON.read_text())
