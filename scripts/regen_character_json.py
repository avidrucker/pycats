"""Regenerate `pycats/characters/data/<stem>.json` from the Python oracles (#1041).

The shipped character JSON is the serialized form of each `<STEM>_FIGHTER_DATA`
oracle (`pycats/characters/<stem>_cat.py`); the R8 drift-guard
(`tests/test_python_json_drift_guard.py`) asserts the committed file hydrates back
to its oracle. When an oracle changes (here: the #1041 dense hit-box labels), the
JSON must be regenerated to match — this script is that regen.

Formatting matches the committed style exactly: standard 2-space `json.dumps`
object layout, but every *leaf* array (one containing no object — a coordinate
triple, a size pair, a `circles` list) is emitted inline on one line
(`[37, 30, 13]`). This is a pure re-dump: with no oracle change it is a no-op
diff, so a labels-only oracle change produces a labels-only JSON diff.

Run from the repo root:  python -m scripts.regen_character_json
"""

from __future__ import annotations

import json

from pycats.characters.birky_cat import BIRKY_FIGHTER_DATA
from pycats.characters.default_cat import DEFAULT_FIGHTER_DATA
from pycats.characters.gnok_cat import GNOK_FIGHTER_DATA
from pycats.characters.nalio_cat import NALIO_FIGHTER_DATA
from pycats.characters.narz_cat import NARZ_FIGHTER_DATA
from pycats.combat.data import CHARACTER_DATA_DIR, fighter_to_json

# The stem → oracle mapping mirrors the R8 drift-guard's ORACLES. A new flip adds
# its entry here so its JSON regenerates alongside the others.
ORACLES = {
    "nalio": NALIO_FIGHTER_DATA,
    "birky": BIRKY_FIGHTER_DATA,
    "narz": NARZ_FIGHTER_DATA,
    "gnok": GNOK_FIGHTER_DATA,
    "default": DEFAULT_FIGHTER_DATA,
}


def _has_object(value) -> bool:
    """True if `value` is or contains a dict anywhere — such an array is exploded
    (each element on its own line); a purely scalar/array-of-scalars leaf inlines."""
    if isinstance(value, dict):
        return True
    if isinstance(value, list):
        return any(_has_object(element) for element in value)
    return False


def _inline(value) -> str:
    """One-line render of a leaf array (or scalar), `, `-separated — matches the
    committed coordinate/size/`circles` style (`[[20, 15, 14], [20, 45, 14]]`)."""
    if isinstance(value, list):
        return "[" + ", ".join(_inline(element) for element in value) + "]"
    return json.dumps(value)


def format_document(document: dict) -> str:
    """Serialize `document` as the committed character-JSON text: `json.dumps`
    2-space layout with leaf arrays inlined, plus a trailing newline."""

    def render(value, level: int) -> str:
        pad = "  " * level
        child_pad = "  " * (level + 1)
        if isinstance(value, dict):
            if not value:
                return "{}"
            rows = [f"{child_pad}{json.dumps(key)}: {render(val, level + 1)}" for key, val in value.items()]
            return "{\n" + ",\n".join(rows) + "\n" + pad + "}"
        if isinstance(value, list):
            if not _has_object(value):  # leaf array → inline
                return _inline(value)
            rows = [f"{child_pad}{render(element, level + 1)}" for element in value]
            return "[\n" + ",\n".join(rows) + "\n" + pad + "]"
        return json.dumps(value)

    return render(document, 0) + "\n"


def regenerate() -> list[str]:
    """Rewrite every `<stem>.json` from its oracle; return the stems written."""
    written = []
    for stem, fighter in ORACLES.items():
        path = CHARACTER_DATA_DIR / f"{stem}.json"
        path.write_text(format_document(fighter_to_json(fighter, stem)))
        written.append(stem)
    return written


if __name__ == "__main__":
    for stem in regenerate():
        print(f"regenerated {stem}.json")
