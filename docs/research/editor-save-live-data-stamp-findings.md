# Editor Save stamps labels + provenance onto the live `nalio.json` — findings

**Ticket:** #978 (RESEARCH, `combat:editor`) · **Parent:** #792 · **Date:** 2026-07-31 · **Agent:** ELDERBERRY
**Repo under investigation:** `pycats-editor` (private, sibling at `…/Study/Python/pycats-editor`) · **Deliverable:** this doc.

## TL;DR

An interactive `pycats-editor` **Save (the `S` key)** writes to the **live, git-tracked**
`pycats/characters/data/<character>.json` **by design** — that is the default Save
destination. The write re-serializes the whole fighter and (a) stamps a `label` on every
collapsed hit box (#964 hit-letters) and (b) attaches a top-level `provenance` block for the
edited move. Geometry is unchanged, so the git diff is exactly: jab-hitbox `label`s + a
`provenance` block (+ `indent=2` reformatting of any previously-inline arrays). It lands on
`main` and not a copy because `pycats` is installed **editable**, so the data-dir constant
resolves into the real repo checkout.

**It is the editor, not tests/goldens.** No test writes the live file (all editor Save tests
pass an explicit tmp `out_path`); the stamp is the Save-destination default firing on a bare
interactive Save.

This answers the ticket's Q1 (trigger — confirmed) and Q2 (default-to-live — intended but
harmful). Q3 (guard) is a fix decision; the option space is laid out below for a human ruling,
and any fix is a **downstream DEV ticket filed one at a time**, not decided here.

## The code path (verbatim)

**1. The `S`-key handler** — `pycats-editor: __main__.py`, the `event.key == pygame.K_s`
branch of the event loop — calls `save.save` with **no `out_path`**:

```python
elif event.key == pygame.K_s:  # save: collapse per-frame -> windows, write file (E5)
    try:
        path = save.save(work, character, move_key, fighter=fighter)
    ...
        print(f"saved {path}")
```

**2. `save.save` defaults `out_path=None`** — `pycats-editor: save.py::save`:

```python
def save(work, character, move_key, *, fighter=None, out_path=None) -> Path:
    if fighter is None:
        fighter = load_fighter_data(character)
    doc = save_document(fighter, move_key, work, character)
    path = resolve_save_path(character, out_path)
    path.write_text(json.dumps(doc, indent=2) + "\n")
    return path
```

**3. `resolve_save_path(character, None)` → the live shipped file** —
`pycats-editor: save.py::resolve_save_path`:

```python
def resolve_save_path(character, out_path) -> Path:
    if out_path is not None:
        return Path(out_path)
    return CHARACTER_DATA_DIR / f"{character}.json"   # <- the sim's live data file
```

**4. Why it lands on `main` (not a copy) — the editable install.** `CHARACTER_DATA_DIR` is
`pycats: combat/data.py`:

```python
CHARACTER_DATA_DIR = Path(__file__).parent.parent / "characters" / "data"
```

`pycats-editor/pyproject.toml` documents that `pycats` is installed with
`pip install -e ../pycats` (editable, not a PyPI dep). So the `pycats` package `__file__`
points into the real repo checkout, and `CHARACTER_DATA_DIR` resolves to
`…/Study/Python/pycats/pycats/characters/data/` — the tracked directory on the shared `main`.

## Why the diff has that exact shape

`save_document` (`pycats-editor: save.py::save_document`) builds the write payload:

```python
def save_document(fighter, move_key, work, character) -> dict:
    fd = updated_fighter(fighter, move_key, work)     # jab hitboxes -> collapsed (carry labels)
    doc = fighter_to_json(fd, character)              # whole-fighter thin-mirror
    entry = {"frames": provenance_frames(work)}       # top-level provenance for this move
    ...
    doc.setdefault("provenance", {})[move_key] = entry
    return doc
```

- **`label` on each jab hitbox:** `updated_fighter` replaces jab's hitboxes with
  `collapsed_hitboxes(work)`; the collapse (#964) sets `Hitbox.label` to the hit-letter, and
  the public `fighter_to_json` (#940) serializes it. The committed `nalio.json` has no
  `label`s, so they show as additions.
- **Top-level `provenance` block:** attached unconditionally for the edited move
  (`provenance_frames` — the frame-major trace; also carries per-box `label`s). The committed
  file has no `provenance`, so the whole block is an addition.
- **Geometry unchanged:** the jab stays 3-box because Save re-serializes the same collapsed
  windows; only the labels + provenance (and JSON reformatting) differ. This matches the
  observed "jab stays 3-box" in the ticket and in this session's dirtied file (9 `label`s, 1
  `provenance` block, no geometry change).

## Why tests don't catch it — and why it recurs on `main`

Every Save test in `pycats-editor: tests/test_save_e5.py` passes an **explicit tmp
`out_path`** (e.g. `save.save(work, "nalio", "jab", fighter=fighter, out_path=out)` with
`out = tmp_path / "nalio.json"`). So the tests exercise the serializer without ever touching
the live file — the suite stays green and clean. The **interactive** Save is the only caller
that omits `out_path`, so it alone falls through to the live-file default. That asymmetry is
why the dirty-checkout only appears after **hands-on editor sessions**, and why it has
recurred at claim time for editor tickets **#964, #972, #976** (each reverted by hand), and
again in this session (found dirty on `main`, `git restore`d during #946).

## The design ruling this rests on

The behavior is deliberate. `pycats-editor: save.py` module docstring records the E5/#924
ruling:

> the save destination is an explicit `out_path` that DEFAULTS to the live
> `pycats/characters/data/<character>.json` — so a caller (and the tests) can target a tmp
> path, but a bare Save lands on the data the sim loads (§4; the human reviews the git diff
> before committing it into pycats).

The premise is "the human reviews the git diff before committing." The recurring dirty-main
shows the gap: the ruling optimizes the *intended authoring* flow (edit → Save → review diff →
commit), but there is **no guard** distinguishing that from an *experimental / accidental*
Save (opening the editor to look, pressing `S` to test it, exploring geometry). Every such
Save dirties a shared tracked checkout that then needs a manual `git restore`, and — per the
ticket — risks reddening the editor suite (which couples to nalio geometry) and, on a fleet
merge, `main`.

<sub>The write does print `saved <path>` to the editor's stdout and caption, so it is not
unannounced — but nothing in that message flags that the resolved path was a *tracked,
shipped* data file rather than a scratch destination.</sub>

## Answers to the ticket's questions

- **Q1 — What triggers the write?** Confirmed: the `S`-key handler calls `save.save(...)`
  with no `out_path`; `out_path` defaults to `None`; `resolve_save_path` returns
  `CHARACTER_DATA_DIR/<character>.json` (the live file). The stamped `label`s come from the
  #964 collapse via `fighter_to_json`; the `provenance` block from `save_document`.
- **Q2 — Is default-to-live intended?** Yes — an explicit E5/#924 ruling (docstring above),
  premised on manual diff-review before commit. The recurrence (#964/#972/#976 + this session)
  is the cost of having no guard for non-authoring Saves.
- **Q3 — Does a guard belong at the seam?** A fix decision, not settled here. Option space:

  | Option | What changes | Trade-off |
  |---|---|---|
  | **A. Default to a scratch dest** | `resolve_save_path` defaults to a non-tracked path (e.g. `repros/<character>.json` or an editor-output dir); writing the live file requires an explicit `out_path`/target. | Bare Save can never dirty `main`; but the intended "edit → land in pycats" flow now needs an explicit target step. |
  | **B. Keep default-to-live, guard the seam** | Save **confirms/refuses** when the resolved destination is a git-tracked shipped data file (prompt, or require a `--force`/explicit-target flag). | Preserves the authoring default; adds a friction gate that stops accidental Saves. Needs a "is this path tracked/shipped?" check. |
  | **C. Both** | Default to scratch **and** guard any write that targets the tracked data dir. | Safest; most behavior change to the current flow. |

  My read (evidence-based, not a decision): **B or C** — the dirtying is by-design and only
  bites the *non-authoring* Save, so a guard at the destination seam addresses the reported
  problem with the least disruption to the intended author flow. **Which option ships is
  Avi's call**, and it lands as a downstream `pycats-editor` DEV ticket filed after the ruling.

## Scope / next step

- This is the RESEARCH closing artifact. **No fix is applied here** (research → findings +
  option space; the fix is a separate DEV ticket, one at a time — RULES "Filing work").
- The fix lives in `pycats-editor` (`save.py::resolve_save_path` and/or `save.py::save`, with
  the guard optionally reading whether the resolved path is under the tracked data dir). File
  that against `pycats-editor`'s work-tracking (this pycats tracker, per the #964/#965/#972/#976
  precedent) once the option is chosen.

## Cross-refs

#792 (editor parent) · #958 (collapse-rule letters) · #964 (hit-letter `label` on collapsed
hitboxes) · #940 (`fighter_to_json` public serializer) · #924 (E5 Save) · #951 (Design B
window model) · #972 / #976 (prior editor tickets that hit the dirty-main at claim time) ·
`pycats-editor: save.py`, `__main__.py` · `pycats: combat/data.py::CHARACTER_DATA_DIR`.
