"""Approval guard over the ``(cat, move_key)`` surface — the cross-repo contract
the editor's gif-map census consumes (#1290, ADR-0022).

## Why this test exists

pycats-editor installs pycats as an editable dependency (ADR-0008), so its
gif-map census — ``pycats-editor:tests/test_e10_gif_map.py::test_map_covers_every_mapped_cats_moves``
— iterates ``load_fighter_data(<cat>).moves`` **live at pycats HEAD**. When a
pycats character-data edit adds / removes / renames a move key, that census turns
red in the *editor* suite. But the pycats close gate
(``.claude/orchestrate.json`` → ``close.verify``) runs only the *pycats* suite,
so the pycats author who made the edit never sees the break — it strands a red for
a later editor agent (the #1199 / #1204 manifestation, symptom-patched in #1280).

ADR-0022 (``docs/adr/0022-cross-repo-move-key-surface-guard.md``, Accepted on
#1281) ratified the fix: pycats owns an approval ("golden") test over the
move-key surface, so a surface change reds **here**, in the suite the author runs.
This is a *pointer*, not enforcement — it names the editor census as the consumer
to update in lockstep. It deliberately does **not** import ``pycats_editor`` or
read ``gif_map.json``: the coupling is bound to a failure message, nothing more.

## The surface

The census iterates ``gif_map.load_map()`` — which maps exactly the four playable
archetypes (``ARCHETYPE_ROSTER`` = nalio, narz, birky, gnok). The intended-default
keys (``default`` / ``P1`` / ``P2`` / ``testcat``) are **not** in the editor map,
so the census never reaches them; enumerating them here would guard surface the
consumer does not read, so this snapshot is scoped to ``ARCHETYPE_ROSTER`` to match
the census domain exactly.

## Updating the snapshot

A move-key surface change is legitimate (a new move, a rename). When you make one
on purpose, re-record the committed snapshot::

    PYCATS_UPDATE_GOLDENS=1 pytest tests/test_1290_move_key_surface.py

then review the ``tests/fixtures/move_key_surface.json`` diff and update the editor
census in lockstep — every newly-added ``(cat, move_key)`` pair must either be
mapped in ``pycats-editor:src/pycats_editor/data/gif_map.json`` or added to the
``_UNMAPPED`` set in the census, or the editor suite goes red.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from pycats.characters.roster import ARCHETYPE_ROSTER
from pycats.combat.data import load_fighter_data

# The committed snapshot: {cat: sorted([move_key, ...])} over ARCHETYPE_ROSTER.
_SNAPSHOT_PATH = Path(__file__).parent / "fixtures" / "move_key_surface.json"

# The cross-repo consumer this surface feeds. A pointer only — this test never
# imports it (see module docstring / ADR-0022).
_CONSUMER = "pycats-editor:tests/test_e10_gif_map.py::test_map_covers_every_mapped_cats_moves"


def _live_surface() -> dict[str, list[str]]:
    """The current ``(cat, move_key)`` surface over the editor-mapped cats."""
    return {cat: sorted(load_fighter_data(cat).moves.keys()) for cat in ARCHETYPE_ROSTER}


def test_move_key_surface_matches_committed_snapshot():
    surface = _live_surface()

    if os.environ.get("PYCATS_UPDATE_GOLDENS") == "1":
        _SNAPSHOT_PATH.write_text(json.dumps(surface, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return  # always passes in update mode

    assert _SNAPSHOT_PATH.exists(), (
        f"Move-key surface snapshot missing: {_SNAPSHOT_PATH}\nRun with PYCATS_UPDATE_GOLDENS=1 to record it."
    )

    expected = json.loads(_SNAPSHOT_PATH.read_text(encoding="utf-8"))
    if surface == expected:
        return

    # Report the drift as a set diff per cat, then point at the consumer to update.
    lines: list[str] = []
    for cat in sorted(set(expected) | set(surface)):
        added = sorted(set(surface.get(cat, [])) - set(expected.get(cat, [])))
        removed = sorted(set(expected.get(cat, [])) - set(surface.get(cat, [])))
        if added:
            lines.append(f"  {cat}: added {added}")
        if removed:
            lines.append(f"  {cat}: removed {removed}")
    diff = "\n".join(lines) or "  (cat set changed)"

    raise AssertionError(
        "The (cat, move_key) surface changed — this is a CROSS-REPO contract.\n"
        f"{diff}\n"
        "If intended: re-record with PYCATS_UPDATE_GOLDENS=1, then update the editor\n"
        f"gif-map census in lockstep ({_CONSUMER}) — every new (cat, move_key) pair\n"
        "must be mapped in gif_map.json or added to that test's _UNMAPPED set, or the\n"
        "editor suite goes red. See docs/adr/0022-cross-repo-move-key-surface-guard.md."
    )
