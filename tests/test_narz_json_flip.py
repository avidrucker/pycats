"""
tests/test_narz_json_flip.py

Third fighter flip (#858, child of #792 editor): Narz ships as
`pycats/characters/data/narz.json` and `load_fighter_data("narz")` resolves it
through the R4 JSON branch (#844).

#1141 retired the Python oracle (`narz_cat.py`): the JSON mirror is now the sole
source, so the former byte-equality-to-oracle guards are gone. What remains here
is the shape of the shipped file itself. Byte-integrity of the hydrate is covered
by test_load_fighter_data_json::test_shipped_json_files_hydrate_cleanly.
"""

import json

from pycats.combat.data import CHARACTER_DATA_DIR

NARZ_JSON = CHARACTER_DATA_DIR / "narz.json"


def test_narz_json_file_ships():
    assert NARZ_JSON.exists(), "the Narz flip must commit pycats/characters/data/narz.json"


def test_migrated_json_has_no_provenance():
    # Migrated data starts with no per-frame trace (§2.4); the editor seeds
    # provenance on first open. The drift-guard (R7) skips moves that lack it.
    assert "provenance" not in json.loads(NARZ_JSON.read_text())
