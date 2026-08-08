# ADR-0022 — guard the pycats move-key surface so an editor-census break reaches the author

- **Status:** Accepted  *(2026-08-05 — owner ruling on #1281)*
- **Date:** 2026-08-05

## Context

A pycats character-data change — a cat **gaining a move** in `characters/data/<cat>.json`
(hydrated into `FighterData.moves` by `combat/data.py::load_fighter_data`) — creates mandatory
downstream work in the **pycats-editor** repo. The editor's reference-GIF census,
`pycats-editor:tests/test_e10_gif_map.py::test_map_covers_every_mapped_cats_moves`, iterates
`load_fighter_data(character).moves` for every mapped cat and asserts each move key either resolves
to a source subaction (`gif_map.resolve_subactions`) or is listed in the test's `_UNMAPPED` set. A
new move key that is neither mapped nor in `_UNMAPPED` turns that census **red**.

The two repos are coupled at runtime but not at their gates:

- The editor installs pycats as an **editable dependency** (`pip install -e ../pycats`, ADR-0008),
  so the census reads pycats's move keys **live at HEAD**. Detection of a new key is therefore not
  the problem — the census sees it immediately.
- The pycats **close gate runs only the pycats suite** (`.claude/orchestrate.json` → `close.verify`:
  ruff + `pytest -q` over `pycats/` + `tests/`). It never runs the editor suite. So the author who
  adds the move gets **no signal at their own close** that they have reddened the editor census.

**Manifested:** #1199 (narz `down_b` / `down_b_riposte`) + #1204 (narz `neutral_b`) added move keys
with no narz special reference-GIF dirs; the editor census went red and was caught later by
DRAGONFRUIT, not by the authoring close. The symptom was fixed in #1280 (the three keys added to
`_UNMAPPED`). This decision is the durable guard so the *next* move-addition surfaces at the
author's own gate instead of stranding a red for a later agent.

The gap is precisely **when and who**: the break is detectable, but only in a suite the author does
not run. Any fix must be judged on whether it puts the signal in front of the person making the
change, at the moment they make it.

### Options considered

- **Option A — pycats-side signal.** pycats carries a check that fires when the move-key surface
  changes, landing the signal inside the pycats suite (which the close gate runs). Concretely: an
  approval ("golden") test over the set of `(cat, move_key)` pairs. Adding, removing, or renaming a
  key trips it; its failure message names the downstream editor census as the consumer to update in
  lockstep. The author updates a committed pycats snapshot **and** is pointed at the editor work in
  the same red-to-green cycle.

- **Option B — editor pins a pycats SHA.** The editor stops tracking pycats at HEAD and pins a
  known-good commit; bumping the pin becomes a deliberate, suite-run editor step. A pycats data
  change reaches the editor only through an explicit bump.

- **Option C — cross-repo CI.** A job runs the editor suite against pycats HEAD on every pycats
  change. Rejected: this repo has no CI; work is gated locally through `pmtools` + the fleet close
  gate. Standing up cross-repo CI is disproportionate to the defect and out of scope.

- **Option D — relax the census to warn, not fail, on an unknown key.** Rejected: it removes the
  red without replacing the guarantee, so an un-grounded move key ships with no reference and no
  gate — trading a caught break for an uncaught one.

## Decision

**Adopt Option A.** pycats owns an approval test over its **move-key surface** — the set of
`(cat, move_key)` pairs across the cats the editor maps — committed as a reviewed snapshot. The
test is red the moment the surface changes and green only once the snapshot is updated; its failure
message states, in one line, that the move-key surface is a cross-repo contract and names the
editor census (`pycats-editor:tests/test_e10_gif_map.py`) as the consumer to update in the same
change.

We will **not** adopt Option B. B genuinely decouples the repos, but it relocates the defect rather
than fixing it: the pycats author still gets no signal at their close, and the break instead lands
on whoever later bumps the editor's pin — the same "caught later by someone else" failure #1281
exists to kill, moved one repo over. B also reverses ADR-0008's editable-install model and adds
version-drift management (a pinned editor that lags pycats HEAD until a deliberate bump). The
ticket's stated defect is "no **author-side** signal at pycats-close time"; A targets that directly
and B does not.

### The coupling A adds, and its bound

A adds cross-repo *awareness* to the pycats gate — the trade-off #1281 asks the architect to
resolve. We bound it deliberately: pycats does **not** import editor code, read `gif_map.json`, or
know which keys are mapped. The pycats test only asserts that the move-key set is a **reviewed
surface** and that changing it is a deliberate act with a named downstream consumer. The editor
knowledge is confined to a **pointer in a failure message**, not a dependency. This is the minimal
viable coupling: enough to route the author to the editor work, not enough to make pycats depend on
the editor.

## Consequences

**Easier**

- The author who adds a move key sees a red in the **pycats** suite — the one their close gate runs
  — with a message pointing at the exact editor follow-up. The break can no longer strand silently
  for a later agent.
- One source of truth stays in pycats (ADR-0008's editable install is preserved); the editor keeps
  tracking pycats HEAD with no pin to manage.
- The guard is able-to-fail by construction: adding a key without updating the snapshot is red;
  updating both is green — the same red-green discipline every pycats bugfix already follows.

**Harder / accepted**

- Every legitimate move addition now trips one extra approval test and requires a one-line snapshot
  update — deliberate friction, and the point: it is the checkpoint that makes the author look at
  the cross-repo consumer.
- The signal is a **pointer**, not an enforcement: pycats reminds the author to update the editor
  census; it cannot prove they did (pycats does not run the editor suite). The remaining editor-side
  gate is the census test itself. A pins the reminder at the right time and place; it does not, and
  is not meant to, run the editor suite from pycats.
- pycats's gate carries one sentence of editor awareness. Bounded to a failure-message pointer (see
  above), this is accepted as the minimal coupling.

**Follow-on work (not part of this ADR — design-only ticket)**

- A DEV ticket implements the pycats-side approval test over the `(cat, move_key)` surface, with the
  cross-repo pointer in its failure message and a committed snapshot fixture. Filed downstream on the
  owner's ruling, one at a time.
- The editor census (`_UNMAPPED`) remains the editor-side gate; no change to it here (the #1280
  symptom fix already landed).

## Refs

Editor census `pycats-editor:tests/test_e10_gif_map.py::test_map_covers_every_mapped_cats_moves`
(#986, parent #792); editable-install coupling ADR-0008; trigger commits `684cd5a` (#1199),
`0eb3058` (#1204); symptom fix #1280; this decision #1281.
