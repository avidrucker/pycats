# pycats-editor `save_document` drops other moves' provenance — findings

> **Agent:** BANANA · **Authored:** 2026-08-09 · **Ticket:** #1322

## Verdict

**CONFIRMED by execution.** `pycats_editor.save.save_document` writes a document whose
`provenance` dict contains only the move just saved; every other move's provenance is
dropped. The docstring's guarantee — *"existing provenance for other moves is preserved"* —
does not hold. The defect is **latent on pristine data** (no shipped character file carries
a `provenance` key) and bites on the **second save** of a file that already has one.

The suspected mechanism in the ticket is correct **but incomplete**: the loss is a
**two-stage round-trip failure**, not merely the `setdefault` observation. See *Mechanism*.

## Repro (executed, not read)

Run against `pycats-editor @ 5979479` + `pycats @ main`, with the editor venv:

```
cd ~/Documents/Study/Python/pycats-editor && .venv/bin/python <repro>
```

`<repro>` (the ticket's script, plus three supporting-fact probes):

```python
import json, copy
from pycats.combat.data import _fighter_from_json, fighter_to_json
from pycats_editor import save as S
from pycats_editor.working import working_move_from_fighter

CHAR = "nalio"
raw = json.load(open(f"pycats/characters/data/{CHAR}.json"))

a, b = [k for k, v in raw["moves"].items() if v.get("hitboxes")][:2]

f1 = _fighter_from_json(copy.deepcopy(raw))
doc1 = S.save_document(f1, a, working_move_from_fighter(f1, a), CHAR)

f2 = _fighter_from_json(copy.deepcopy(doc1))          # reopen what we just saved
doc2 = S.save_document(f2, b, working_move_from_fighter(f2, b), CHAR)
```

Observed:

```
A) shipped nalio.json has 'provenance' key: False
B) 'provenance' in fighter_to_json(...): False

editing two moves in sequence: 'attack' then 'jab'
after saving 'attack'     -> provenance: ['attack']
after saving 'jab'        -> provenance: ['jab']

LOST: ['attack']
C) doc1 carried provenance: True | reopened doc has it as FighterData attr: False
```

The observation matches the ticket's report exactly (`['attack'] -> ['jab']`, `LOST: ['attack']`).

## Mechanism — confirmed, and refined

The ticket suspected the loss lived entirely in `save_document`'s tail:

```python
doc = fighter_to_json(fd, character)
...
doc.setdefault("provenance", {})[move_key] = entry
```

That is one half. `setdefault` *would* preserve an existing `provenance` dict — but the
dict handed to it never contains one, for **two independent reasons**, either of which
alone is sufficient to lose the data:

1. **`fighter_to_json` never emits `provenance`.** Probe **B** returns `False`:
   `"provenance" in fighter_to_json(_fighter_from_json(raw), "nalio")` is `False`. So the
   `doc` that `setdefault` runs against has no `provenance` key, and `setdefault` always
   creates a **fresh** dict holding only `move_key`. Grounded in `pycats/combat/data.py`:
   the `fighter_to_json` region documents *"`provenance` is never written"*, and its guard
   comment notes *"`doc["provenance"]` is NEVER read here"*.

2. **`_fighter_from_json` drops `provenance` on load.** Probe **C** shows `doc1` *did*
   carry `provenance` (the first save wrote it), yet the reopened `FighterData` has no such
   attribute — `hasattr(f2, "provenance")` is `False`. `FighterData` structurally cannot
   hold provenance; the loader's docstring states it *"Drops schema-level keys
   (schema_version, character, provenance)"*.

**Consequence:** the `setdefault` "preserve" branch is **unreachable** in any path where
`doc` comes from `fighter_to_json` — which is every path. This is dead code, not a
sometimes-fires guard.

**The reopen in the repro is incidental to the loss.** Because the editor's live save flow
(`__main__.py._open_save_prompt` → `save.save_document(fighter, move_key, work, character)`)
builds the doc from the in-memory `fighter` — a `FighterData` that never carried provenance
— **every** `save_document` call emits a doc whose `provenance` is exactly `{the one move
being saved}`. Overwriting any path that already holds provenance therefore drops it,
whether or not the file was reopened between saves. The reopen only makes the loss
observable within a single script.

## Blast radius

- **No committed loss.** All **6** shipped `pycats/characters/data/*.json` files were
  scanned; **none** carries a top-level `provenance` key (probe **A** confirms for nalio;
  the loop confirmed the other five). A first save cannot lose what was never there, so no
  authored provenance is degraded in the git-tracked data.
- **Working trees:** cannot be inspected from here. Any uncommitted `<character>.json` that
  a user has saved twice through the editor would already have lost all but the
  last-saved move's provenance. The exposure is bounded to un-committed local files; there
  is nothing to recover in the repo.
- **Downstream effect (why it matters):** `provenance.frames` is what makes reopen
  **exact**. A move whose provenance was dropped falls back to reverse-collapse, which is
  lossy — and separately suspected (row 8 of #1323) of minting duplicate `label` values.
  So the defect quietly downgrades every previously-authored move in a file to the lossy
  reopen path the provenance mechanism exists to avoid.

## Where the fix belongs (option space — ruling is downstream)

Two shapes, with different blast radii. **This ticket surfaces the options; it does not
rule.** The fix DEV ticket (and, if Option 2 is chosen, a `decision:` ticket) are filed
one-at-a-time downstream.

| | Option 1 — merge at the write layer | Option 2 — `FighterData` carries provenance |
|---|---|---|
| **Change** | Before writing, read the prior on-disk doc's `provenance` dict and merge the current move's entry into it. Belongs at a layer that knows the resolved destination path (`save.save()` / the `write_document` call sites), **not** in `save_document`, which is pure (takes fighter+work, returns a dict; has no path). | Add a `provenance` field to `FighterData`; have `_fighter_from_json` load it and `fighter_to_json` emit it, so the load→save round-trip preserves it structurally. |
| **Blast radius** | Localized to `pycats-editor/save.py`. No pycats schema/data-model change. | pycats **core data-model change**: `FighterData`, `_fighter_from_json`, `fighter_to_json`, and the drift-guard test (R7) that consumes `doc["provenance"]`. Schema implications for every character file. |
| **Wrinkle** | The #983 prompt has O/S/B/N destinations (Both writes two files); the merge must be per-resolved-destination, so a Scratch save merges against the scratch file, not the live one. | An editor-only concern leaks into the sim's data model; needs a design decision on whether provenance becomes a first-class schema key. |
| **Verdict** | **Recommended** — lower blast radius, keeps the change inside the editor. | Defer behind a `decision:` ticket; it is a data-model change, not a bug-fix. |

**Recommendation:** fix via **Option 1** (merge existing destination provenance at write
time, keyed by the resolved path), and file Option 2 separately as a `decision:` ticket
only if reopen-exactness is later wanted as a structural guarantee rather than an
editor-write concern.

## Docstring correction (downstream, sibling repo)

`save_document`'s docstring asserts a guarantee the code does not provide:

> "...with the `provenance` trace attached for the edited move (existing provenance for
> other moves is preserved)."

The parenthetical is false and must be corrected as part of the fix DEV ticket. Editing
`pycats-editor/src/pycats_editor/save.py` is a change to the **sibling repo** and is out of
scope for this research ticket — it rides with the downstream DEV fix.

## DoD status

- [x] **Red / non-vacuous repro** demonstrating the loss (`['attack'] -> ['jab']`,
      `LOST: ['attack']`), failing for the stated reason on current `main` — done by
      execution. The committed **red-green pytest** belongs to the downstream fix DEV
      ticket (it lives in `pycats-editor/tests/` — sibling repo, gated on your OK).
- [x] **Mechanism confirmed** (not merely assumed): two-stage round-trip loss — `_fighter_from_json`
      drops provenance on load **and** `fighter_to_json` never emits it, making the
      `setdefault` preserve-branch dead code. Evidence: probes A/B/C above.
- [x] **Blast radius:** no committed loss (0 of 6 shipped files carry provenance);
      exposure bounded to un-committed local files; nothing to recover in the repo.
- [x] **Fix-location decision surfaced:** Option 1 (merge at write layer) recommended;
      Option 2 (`FighterData` carries provenance) deferred behind a `decision:` ticket.
- [x] **Docstring correction identified** (false parenthetical) — routed to the downstream
      DEV fix, as it edits the sibling repo.

## Follow-ups (file one-at-a-time downstream of this doc)

1. **DEV (pycats-editor):** implement Option 1 (merge destination provenance at write time)
   + correct the `save_document` docstring + land the red-green pytest. Sibling-repo work.
2. **`decision:` (optional):** whether `FighterData` should carry `provenance` as a
   first-class schema key (Option 2) — only if structural reopen-exactness is wanted.

## Refs

#1322 (this ticket) · #1323 (row 1, tracker) · #1307 (React port ruling) · #924 (E5
save/collapse) · #792 (editor tracker) · pycats-react-editor#4 (the extraction that
surfaced it)
