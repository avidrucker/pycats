"""
tests/test_nalio_json_flip.py

First fighter flip (#851, child of #792 editor): Nalio ships as
`pycats/characters/data/nalio.json` and `load_fighter_data("nalio")` resolves it
through the R4 JSON branch (#844).

#1141 retired the Python oracle (`nalio_cat.py`): the JSON mirror is now the sole
source, so the former byte-equality-to-oracle guards are gone. What remains here
is the shape of the shipped file itself. Byte-integrity of the hydrate is covered
by test_load_fighter_data_json::test_shipped_json_files_hydrate_cleanly.
"""

import json

from pycats.combat.data import CHARACTER_DATA_DIR

NALIO_JSON = CHARACTER_DATA_DIR / "nalio.json"


def test_nalio_json_file_ships():
    assert NALIO_JSON.exists(), "the Nalio flip must commit pycats/characters/data/nalio.json"


def test_migrated_json_has_no_provenance():
    # Migrated data starts with no per-frame trace (§2.4); the editor seeds
    # provenance on first open. The drift-guard (R7) skips moves that lack it.
    assert "provenance" not in json.loads(NALIO_JSON.read_text())
