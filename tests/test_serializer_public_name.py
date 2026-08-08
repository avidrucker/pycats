"""
tests/test_serializer_public_name.py

#940 (child of #792 editor): the FighterData JSON serializer is promoted from the
underscore-private name to a public ``fighter_to_json``, so the out-of-repo
pycats-editor Save (E5, #924) can depend on a stable public name rather than
reaching into a private one (human ruling: "promote to public first").

Able-to-fail: before the rename the public import raises ``ImportError``; a
lingering private alias makes ``test_private_serializer_name_is_gone`` red.
"""

import json

from pycats.combat import data as data_mod
from pycats.combat.data import (
    CHARACTER_DATA_DIR,
    fighter_to_json,
    load_fighter_data,
)

NALIO_JSON = CHARACTER_DATA_DIR / "nalio.json"

_PRIVATE_NAME = "_" + "fighter_to_json"  # avoid a literal a token-rename could catch


def test_public_serializer_matches_on_disk():
    # The public name serializes byte-for-byte what ships on disk. Able-to-fail:
    # the public symbol is absent before the rename -> ImportError at collection.
    on_disk = json.loads(NALIO_JSON.read_text())
    assert fighter_to_json(load_fighter_data("nalio"), "nalio") == on_disk


def test_private_serializer_name_is_gone():
    # One canonical public name — no private second name dangling on the module.
    # Able-to-fail: keeping the private alias keeps the attribute present -> red.
    assert not hasattr(data_mod, _PRIVATE_NAME)
