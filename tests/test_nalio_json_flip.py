"""
tests/test_nalio_json_flip.py

First fighter flip (#851, child of #792 editor): Nalio now ships as
`pycats/characters/data/nalio.json` and `load_fighter_data("nalio")` resolves it
through the R4 JSON branch (#844) instead of the Python switch.

The Python literal (`nalio_cat.py` NALIO_FIGHTER_DATA) is retained as the
round-trip ORACLE and fallback (Risk 1 mitigation, ruling on #847). These tests
prove the on-disk file hydrates back byte-equal to that oracle — the guarantee
that keeps the flip golden-safe. Corrupting a value in the committed JSON breaks
the equality below.
"""

import json

from pycats.characters.nalio_cat import NALIO_FIGHTER_DATA
from pycats.combat.data import (
    CHARACTER_DATA_DIR,
    _fighter_to_json,
    load_fighter_data,
)

NALIO_JSON = CHARACTER_DATA_DIR / "nalio.json"


def test_nalio_json_file_ships():
    assert NALIO_JSON.exists(), "the Nalio flip must commit pycats/characters/data/nalio.json"


def test_nalio_loads_from_json_equals_python_oracle():
    # load_fighter_data("nalio") now hits the JSON branch (the file exists), so
    # this asserts the on-disk file hydrates to the exact Python data. Able-to-fail:
    # a wrong value in nalio.json makes the hydrated FighterData != the oracle.
    assert load_fighter_data("nalio") == NALIO_FIGHTER_DATA


def test_committed_json_matches_serializer():
    # Guards against a stale / hand-edited file: the committed bytes must parse to
    # exactly what the R5 serializer emits for the current Python literal. If the
    # Python changes and the JSON is not regenerated, this fails and names nothing
    # ambiguous — regenerate the dump.
    on_disk = json.loads(NALIO_JSON.read_text())
    assert on_disk == _fighter_to_json(NALIO_FIGHTER_DATA, "nalio")


def test_migrated_json_has_no_provenance():
    # Migrated data starts with no per-frame trace (§2.4); the editor seeds
    # provenance on first open. The drift-guard (R7) skips moves that lack it.
    assert "provenance" not in json.loads(NALIO_JSON.read_text())
