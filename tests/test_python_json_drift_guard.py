"""
tests/test_python_json_drift_guard.py

R8 — Python↔JSON round-trip drift-guard (#877, child of #792 editor via SCOPE
#826). Sibling of the R7 provenance drift-guard (#863): R7 guards a JSON file's
per-frame `provenance` against its own committed `hitboxes`; **R8 guards a
flipped fighter's shipped JSON against its Python oracle** (`<STEM>_FIGHTER_DATA`).

Four fighters are flipped (nalio/birky/narz/gnok, #851/#856/#858/#860):
`load_fighter_data("<stem>")` hydrates `characters/data/<stem>.json` via the R4
JSON branch (#844), while the `<STEM>_FIGHTER_DATA` literal is the maintained
oracle. This module holds the invariant "the shipped JSON hydrates to the Python
oracle" in ONE place, across every flip at once, instead of leaving it to the
incidental per-fighter `loads_from_json_equals_python_oracle` test.

The gap this closes already reddened main: #841 merged f/u/d-tilt into
`gnok_cat.py` on top of the #860 gnok.json flip WITHOUT regenerating gnok.json →
12 failing until hotfix a60869c. This guard fails the moment any flipped
fighter's Python literal and its committed JSON disagree, for present and future
flips alike.
"""

import pytest

from pycats.characters.birky_cat import BIRKY_FIGHTER_DATA
from pycats.characters.default_cat import DEFAULT_FIGHTER_DATA
from pycats.characters.gnok_cat import GNOK_FIGHTER_DATA
from pycats.characters.nalio_cat import NALIO_FIGHTER_DATA
from pycats.characters.narz_cat import NARZ_FIGHTER_DATA
from pycats.combat.data import CHARACTER_DATA_DIR, load_fighter_data

# The maintained Python literal for each flipped fighter, keyed by the JSON stem
# `load_fighter_data` resolves. A new flip MUST add its oracle here — the
# registry-completeness guard below fails loudly (naming the stem) otherwise.
# "default" is the default cat's flip (#887/#881): default.json is the sole
# runtime source, and DEFAULT_FIGHTER_DATA is demoted to this oracle + gnok/narz's
# construction base (never a runtime path).
ORACLES = {
    "nalio": NALIO_FIGHTER_DATA,
    "birky": BIRKY_FIGHTER_DATA,
    "narz": NARZ_FIGHTER_DATA,
    "gnok": GNOK_FIGHTER_DATA,
    "default": DEFAULT_FIGHTER_DATA,
}


@pytest.mark.parametrize("stem", sorted(ORACLES))
def test_shipped_json_hydrates_to_python_oracle(stem):
    # load_fighter_data takes the JSON branch (the file exists), so this compares
    # hydrated-JSON vs the Python literal — the exact drift #841 introduced.
    # Hand-editing a value in the committed <stem>.json without touching the
    # oracle turns this red for that stem.
    assert load_fighter_data(stem) == ORACLES[stem], (
        f"{stem}.json hydrates to a FighterData that differs from "
        f"{stem.upper()}_FIGHTER_DATA — regenerate the JSON from the Python "
        f"oracle (or reconcile the oracle to the JSON)."
    )


def test_every_shipped_json_has_a_registered_oracle():
    # A future flip that ships characters/data/<stem>.json but forgets to add its
    # oracle above would otherwise go unguarded. Fail loudly and name the stem.
    shipped = {p.stem for p in CHARACTER_DATA_DIR.glob("*.json")}
    assert shipped == set(ORACLES), (
        "every shipped fighter JSON must have a registered Python oracle in "
        f"ORACLES; unregistered={sorted(shipped - set(ORACLES))}, "
        f"registered-but-missing={sorted(set(ORACLES) - shipped)}"
    )
