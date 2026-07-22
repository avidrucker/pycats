"""
tests/test_drift_guard.py

R7 (#863, child of #792): the drift-guard (design §2.3). For each shipped
`<character>.json` that carries a `provenance` block, recompile the per-frame
trace through R6's `collapse` (#862) and assert it reproduces the committed
canonical `hitboxes`. A mismatch means someone hand-edited the canonical boxes
without updating the trace (or vice-versa) — the guard fails and names the move.

Moves with no `provenance` entry are skipped: today's four shipped fighters were
migrated with no per-frame trace (§2.4), so the shipped sweep below is vacuously
green right now. It is the standing guard that activates automatically the first
time the editor (E5) writes provenance into a file.

Scope: this guards **hitboxes** only. §2.3 also names the per-move `hurtbox`
override, but R6 built only the hitbox collapse — the per-frame hurtbox-union
collapse (§1.2) does not exist yet, so guarding it is a follow-up (needs that
collapse first), deliberately out of scope here.
"""

import json

from pycats.characters.nalio_cat import NALIO_FIGHTER_DATA
from pycats.combat.collapse import collapse
from pycats.combat.data import (
    CHARACTER_DATA_DIR,
    _fighter_from_json,
    _fighter_to_json,
)

# The design §1.1 worked example: Nalio jab per-frame trace (frames 2 & 3
# identical, all three boxes). Collapsing this must reproduce _JAB.hitboxes.
_JAB_FRAMES = [
    {
        "frame": 2,
        "boxes": [
            {"id": 0, "circle": [54, 27, 19], "damage": 3.0, "angle": 83, "kbg": 100.0, "wdsk": 20},
            {"id": 1, "circle": [44, 28, 13], "damage": 3.0, "angle": 83, "kbg": 100.0, "wdsk": 20},
            {"id": 2, "circle": [34, 29, 15], "damage": 3.0, "angle": 85, "kbg": 100.0, "wdsk": 20},
        ],
    },
    {
        "frame": 3,
        "boxes": [
            {"id": 0, "circle": [54, 27, 19], "damage": 3.0, "angle": 83, "kbg": 100.0, "wdsk": 20},
            {"id": 1, "circle": [44, 28, 13], "damage": 3.0, "angle": 83, "kbg": 100.0, "wdsk": 20},
            {"id": 2, "circle": [34, 29, 15], "damage": 3.0, "angle": 85, "kbg": 100.0, "wdsk": 20},
        ],
    },
]


def _drift_mismatches(doc: dict) -> list[str]:
    """Move keys whose committed `hitboxes` disagree with their recompiled provenance.

    The §2.3 guard: hydrate the doc, and for each move with a `provenance` frames
    entry, run R6 `collapse` over that trace and compare to the committed
    hitboxes. Moves with no provenance are skipped. Returns the drifting keys
    (empty == no drift), so a failure can name the move.
    """
    fighter = _fighter_from_json(doc)
    mismatches = []
    for move_key, entry in doc.get("provenance", {}).items():
        frames = entry.get("frames")
        if not frames:
            continue
        move = fighter.moves[move_key]
        recompiled = collapse(frames, startup=move.startup, active=move.active)
        if recompiled != move.hitboxes:
            mismatches.append(move_key)
    return mismatches


def test_shipped_json_provenance_matches_hitboxes():
    # For every shipped file: any move carrying provenance must recompile to its
    # committed hitboxes. Vacuously green today (migrated data has no provenance);
    # the assertion still runs so a future provenance-bearing file is guarded.
    for path in sorted(CHARACTER_DATA_DIR.glob("*.json")):
        doc = json.loads(path.read_text())
        assert _drift_mismatches(doc) == [], f"{path.name} has canonical/provenance drift"


def _nalio_jab_fixture() -> dict:
    # A real, hydratable fighter (so _fighter_from_json succeeds) carrying a
    # provenance trace for its jab — the §1.1 worked example. Serialize the real
    # Nalio, then attach the per-frame jab trace the migrated file lacks.
    doc = _fighter_to_json(NALIO_FIGHTER_DATA, "nalio")
    doc["provenance"] = {"jab": {"note": "§1.1 worked example fixture", "frames": _JAB_FRAMES}}
    return doc


def test_drift_guard_passes_when_provenance_matches():
    # The jab trace collapses to exactly the committed jab hitboxes → no drift.
    doc = _nalio_jab_fixture()
    assert doc["moves"]["jab"]["hitboxes"]  # sanity: the move is present
    assert _drift_mismatches(doc) == []


def test_drift_guard_catches_hand_edited_hitbox():
    # Able-to-fail: edit a canonical hitbox value (damage 3.0 → 9.0) WITHOUT
    # touching the provenance trace. The recompiled boxes no longer match the
    # committed ones, so the guard fires and names "jab".
    doc = _nalio_jab_fixture()
    doc["moves"]["jab"]["hitboxes"][0]["damage"] = 9.0
    assert _drift_mismatches(doc) == ["jab"]
