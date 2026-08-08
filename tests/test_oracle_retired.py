"""
tests/test_oracle_retired.py

Retirement guard (#1141, routed by #1078 Q1/G1, under #792 editor): the shipped
`characters/data/<stem>.json` mirror is the SOLE source for the five formerly
oracle'd cats, so the hand-written Python oracles `<stem>_cat.py` are gone.

Background: #881 made the JSON the sole *runtime* source (`load_fighter_data`
returns the hydrated JSON; `_default_fighter` hydrates default.json). The Python
literals survived only as R8 drift-guard oracles and gnok/narz construction bases
— test-only artifacts that reddened on every editor geometry edit and could not be
reconciled (`regen_character_json` dumped *from* the oracle). #1141 retires them.

Able-to-fail: restore any `<stem>_cat.py` and the existence assertion reds; make
any `pycats.characters.<stem>_cat` importable again and the import assertion reds.
"""

import importlib

import pytest

from pycats.combat.data import CHARACTER_DATA_DIR

# The five cats whose JSON mirror is now the sole source (#851/#856/#858/#860/#881).
RETIRED_STEMS = ["nalio", "birky", "narz", "gnok", "default"]

# characters/data/<stem>.json lives at characters/data/; the oracle .py lived one
# level up at characters/<stem>_cat.py.
_CHARACTERS_DIR = CHARACTER_DATA_DIR.parent


@pytest.mark.parametrize("stem", RETIRED_STEMS)
def test_oracle_python_file_is_gone(stem):
    path = _CHARACTERS_DIR / f"{stem}_cat.py"
    assert not path.exists(), (
        f"{path.name} must be deleted — the {stem}.json mirror is the sole source "
        f"(#1141). A restored oracle re-introduces the editor-edit drift trap."
    )


@pytest.mark.parametrize("stem", RETIRED_STEMS)
def test_oracle_module_is_not_importable(stem):
    module = f"pycats.characters.{stem}_cat"
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module(module)


def test_regen_script_is_gone():
    # regen_character_json.py dumped JSON FROM the oracles; with no oracle it has
    # nothing to regenerate and would overwrite editor edits. Retired with them.
    script = _CHARACTERS_DIR.parents[1] / "scripts" / "regen_character_json.py"
    assert not script.exists(), "scripts/regen_character_json.py must be deleted (#1141)"
