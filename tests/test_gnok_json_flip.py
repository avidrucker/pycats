"""
tests/test_gnok_json_flip.py

Fourth fighter flip (#860, child of #792 editor): Gnok ships as
`pycats/characters/data/gnok.json` and `load_fighter_data("gnok")` resolves it
through the R4 JSON branch (#844).

#1141 retired the Python oracle (`gnok_cat.py`): the JSON mirror is now the sole
source, so the former byte-equality-to-oracle guards are gone. What remains here
is the shape of the shipped file itself. Byte-integrity of the hydrate is covered
by test_load_fighter_data_json::test_shipped_json_files_hydrate_cleanly.
"""

import json

from pycats.combat.data import CHARACTER_DATA_DIR

GNOK_JSON = CHARACTER_DATA_DIR / "gnok.json"


def test_gnok_json_file_ships():
    assert GNOK_JSON.exists(), "the Gnok flip must commit pycats/characters/data/gnok.json"


def test_migrated_json_has_no_provenance():
    # Migrated data starts with no per-frame trace (§2.4); the editor seeds
    # provenance on first open. The drift-guard (R7) skips moves that lack it.
    assert "provenance" not in json.loads(GNOK_JSON.read_text())
