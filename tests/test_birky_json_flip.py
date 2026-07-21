"""
tests/test_birky_json_flip.py

Second fighter flip (#856, child of #792 editor): Birky now ships as
`pycats/characters/data/birky.json` and `load_fighter_data("birky")` resolves it
through the R4 JSON branch (#844) instead of the Python switch. Mirrors the Nalio
flip (#851, tests/test_nalio_json_flip.py).

The Python literal (`birky_cat.py` BIRKY_FIGHTER_DATA) is retained as the
round-trip ORACLE and fallback (Risk 1 mitigation, ruling on #847). These tests
prove the on-disk file hydrates back byte-equal to that oracle — the guarantee
that keeps the flip golden-safe. Corrupting a value in the committed JSON breaks
the equality below.
"""

import json

from pycats.characters.birky_cat import BIRKY_FIGHTER_DATA
from pycats.combat.data import (
    CHARACTER_DATA_DIR,
    _fighter_to_json,
    load_fighter_data,
)

BIRKY_JSON = CHARACTER_DATA_DIR / "birky.json"


def test_birky_json_file_ships():
    assert BIRKY_JSON.exists(), "the Birky flip must commit pycats/characters/data/birky.json"


def test_birky_loads_from_json_equals_python_oracle():
    # load_fighter_data("birky") now hits the JSON branch (the file exists), so
    # this asserts the on-disk file hydrates to the exact Python data. Able-to-fail:
    # a wrong value in birky.json makes the hydrated FighterData != the oracle.
    assert load_fighter_data("birky") == BIRKY_FIGHTER_DATA


def test_committed_json_matches_serializer():
    # Guards against a stale / hand-edited file: the committed bytes must parse to
    # exactly what the R5 serializer emits for the current Python literal.
    on_disk = json.loads(BIRKY_JSON.read_text())
    assert on_disk == _fighter_to_json(BIRKY_FIGHTER_DATA, "birky")


def test_migrated_json_has_no_provenance():
    # Migrated data starts with no per-frame trace (§2.4); the editor seeds
    # provenance on first open. The drift-guard (R7) skips moves that lack it.
    assert "provenance" not in json.loads(BIRKY_JSON.read_text())
