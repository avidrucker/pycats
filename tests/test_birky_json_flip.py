"""
tests/test_birky_json_flip.py

Second fighter flip (#856, child of #792 editor): Birky ships as
`pycats/characters/data/birky.json` and `load_fighter_data("birky")` resolves it
through the R4 JSON branch (#844).

#1141 retired the Python oracle (`birky_cat.py`): the JSON mirror is now the sole
source, so the former byte-equality-to-oracle guards are gone. What remains here
is the shape of the shipped file itself. Byte-integrity of the hydrate is covered
by test_load_fighter_data_json::test_shipped_json_files_hydrate_cleanly.
"""

import json

from pycats.combat.data import CHARACTER_DATA_DIR

BIRKY_JSON = CHARACTER_DATA_DIR / "birky.json"


def test_birky_json_file_ships():
    assert BIRKY_JSON.exists(), "the Birky flip must commit pycats/characters/data/birky.json"


def test_migrated_json_has_no_provenance():
    # Migrated data starts with no per-frame trace (§2.4); the editor seeds
    # provenance on first open. The drift-guard (R7) skips moves that lack it.
    assert "provenance" not in json.loads(BIRKY_JSON.read_text())
