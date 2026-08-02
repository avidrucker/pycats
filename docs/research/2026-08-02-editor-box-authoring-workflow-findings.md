# Editor box-authoring workflow — walkthrough, gap list, git-pain playbook

**Ticket:** #1072 (RESEARCH, `combat:editor`, child of #792) · **Date:** 2026-08-02 · **Author:** FIG

## What this answers

Before authoring every move's hit/hurtboxes across the roster with `pycats-editor`, we need
a written, repeatable recipe and a clear list of what the editor can't yet do — so the
campaign runs smoothly instead of fighting the drift-guard, goldens, and two-repo coupling.
This doc delivers five things the ticket asked for:

1. **Capability census** — what the editor does *today*, verified against the `pycats-editor`
   source at HEAD (not the spec).
2. **The end-to-end walkthrough** — a numbered operator recipe for one move, start to finish.
3. **The git-pain playbook** — every way this campaign can redden `main`, and how to avoid it.
4. **The gap list** — what's missing, prioritized, mapped to existing slices/issues or flagged new.
5. **Routing** — which gaps are prerequisites vs nice-to-have. Option space only; **the build
   order is a decision for the human downstream, not made here.**

> **Verified vs inferred.** The census (§1) and the git-pain mechanics (§3) are read from source
> at `pycats-editor` HEAD `68f3b60` (through #1035) and `pycats` `main`. Where a claim is a
> deduction rather than a direct reading, it is marked **[inferred]**. Evidence-sufficiency is
> Avi's call — §4/§5 flag uncertainty rather than gating the campaign.

---

## Headline: the spec lists features that aren't built yet

The single most important census result is a **spec-vs-reality gap** in this ticket's own "Have"
section, which listed several editor QoL items as "already open/landed":

| Feature | Ticket said | Reality (source at HEAD) |
|---|---|---|
| Persist zoom across launches | landed (#908) | **not built** — `#908` OPEN; zoom is in-memory, reset to 1.0 each launch; no settings file read/written |
| Add-hitbox on-screen button | landed (#1031) | **not built** — `#1031` OPEN; only the `A` key adds a box; `BUTTONS` is `[Reset, Re-letter]` |
| Used-letter indicator | landed (#1034) | **not built** — `#1034` OPEN; no on-screen "letters consumed" readout |
| Non-box text scaling | landed (#1012) | **not built** — `#1012` OPEN; `vis.py` scales geometry only, fonts fixed |
| Help overlay | landed (#936) | **built** — via `#1007` (F1/`?` toggles `_draw_help`) |

Two further capabilities the MVP list promises are **also not built**: **hurt-box *authoring***
(you cannot add a hurt box; hurt is whole-move only) and **playback loop** (frames only advance
on manual scrub). Both matter for the campaign — see §4.

---

## 1. Capability census (verified against `pycats-editor` HEAD)

Single-window pygame-ce app; all interaction in `src/pycats_editor/__main__.py:main()`.

### Launch

```bash
# from the pycats-editor repo root, using its own venv
.venv/bin/python -m pycats_editor
```

Boots to a hard-coded default (`nalio`, move `jab`); there is **no `--character`/`--move`
CLI flag** — you switch fighter and move in-app. Recognized flags: `--gif <path>`,
`--mario-gifs <dir>`, `--repros-root <dir>`. On boot it prints the fighter's move keys to the
terminal.

### Controls (source: `keybindings.py::_BINDINGS` + the `main()` event loop)

| Key / gesture | Action |
|---|---|
| `←` / `→`, click/drag timeline | scrub frames |
| `[` / `]` | previous / next move |
| `,` / `.` | previous / next character |
| click box, then drag body | select + move box (**current frame only**) |
| drag the white ring handle | resize selected box (radius = centre→cursor) |
| `Tab` | cycle selected box on the frame |
| `+`/`-` (Shift = ×10) | nudge the focused numeric field |
| `A` | add a **hit** box (centred, current frame) |
| `D` | duplicate selected box (offset +15/+15, new id) |
| `Delete` / `Backspace` | delete selected box from the current frame |
| `Ctrl+←` / `Ctrl+→` | extend the selected box's active window onto the prev/next frame (same id/letter) |
| `1` / `2` / `3` | toggle hit / hurt / reference-GIF layer |
| `M` | overlay ↔ side-by-side |
| `PgUp` / `PgDn`, drag GIF corner | scale the reference GIF |
| `Shift+arrows` / drag GIF body / `P` | pan the reference GIF (`P` cycles x-presets 0/100/200) |
| `;` / `'` | previous / next combo sub-animation |
| `X` | cycle window zoom 1× → 1.5× → 2× |
| `S` | **save** (opens an O/S/B/N destination prompt) |
| `Ctrl+Z` / `Ctrl+Y` | undo / redo (includes GIF view) |
| `Ctrl+R` / Reset button | reset move to as-opened state (undoable) |
| `L` / Re-letter button | re-letter hit boxes to dense A, B, C… |
| `Enter` / click note row | edit the per-move note (provenance) |
| `F1` / `?` | help overlay |

### Per-feature status

Legend: ✅ works · 🟡 partial · ❌ not-built.

| MVP / requested feature | Status | Invoked by | Evidence |
|---|---|---|---|
| Load a fighter | ✅ | boot + `,`/`.` | `main` → `load_fighter_data`; `navigation.step_character` |
| Pick a move | ✅ | `[` / `]` | `navigation.step_move` → `_reload` |
| Scrub frames | ✅ | `←`/`→`, timeline | `timeline.step_frame`, `frame_at_x` |
| **Loop playback** | ❌ | — | no auto-play timer / play key anywhere |
| Add a **hit** box | ✅ | `A` | `working.add_box` (`kind="hit"`) |
| **Add a hurt box** | ❌ | — | `add_box` hard-codes `kind="hit"`; hurt only seeded from posture |
| Move / resize / delete a box | ✅ | drag / ring / `Delete` | `working.move_box` / `resize_box` / `remove_box` |
| **Per-frame** box data | 🟡 | `A` / drag / `Ctrl+←→` | **hits are per-frame** (`WorkingMove.frames`); **hurt is whole-move** (`WorkingMove.hurt`), per-frame hurt deferred (#918) |
| Toggle hit/hurt display | ✅ | `1` / `2` | `gifcompare.toggle_layer` |
| Overlay PM reference GIF | ✅ | auto-resolve; `3`, `M` | `gif_map.reference_gif_at`, `compare_mode=OVERLAY` |
| Scale / translate the GIF | ✅ | `PgUp/PgDn`, `Shift+arrows`, `P`, drag | `gifcompare.zoom_view` / `pan_view` / `cycle_preset_x` |
| Window zoom | ✅ | `X` | `zoom.next_scale` (`PRESETS=(1.0,1.5,2.0)`) |
| Save | ✅ | `S` | `save.save_document` / `write_document` |
| Undo / redo | ✅ | `Ctrl+Z` / `Ctrl+Y` | `history.EditHistory` (snapshots GIF view too, #1054) |
| Re-letter labels (#1035) | ✅ | `L` | `working.reletter_move` |
| Label warnings on load (#1056) | ✅ | automatic | `_label_load_report`, `validate_hit_labels` |
| Help overlay (#1007) | ✅ | `F1`/`?` | `_draw_help`, `keybindings.sections()` |
| Add-hitbox **button** (#1031) | ❌ | — | `BUTTONS=[Reset, Re-letter]` only |
| Persist zoom (#908) | ❌ | — | in-memory only; no settings file |
| Used-letter indicator (#1034) | ❌ | — | no such UI |
| Non-box text scaling (#1012) | ❌ | — | `vis.py` scales geometry only |

### Beyond the MVP (already built, not on the original list)

In-app character/move navigation (`[ ] , .`), per-frame window **extend** (`Ctrl+←/→`), combo
sub-animation cycling (`;`/`'`), on-canvas letter+frame-ordinal box labels (`A0`, `A1`…), the
**Save-destination triage** and per-move change-diff readout (the git-pain safety valve, §3),
per-move note/provenance capture, Re-letter (#1035) and load-time label validation (#1056).

### What the editor writes on Save

`S` → `save.save_document(...)` builds a **whole-fighter thin-mirror** dict, then the O/S/B/N
prompt writes it. Key facts:

- **JSON only.** The editor never writes a Python oracle (`<cat>_cat.py`). Serialization uses
  pycats' public `fighter_to_json(fd, character)`.
- **Geometry is stored in author-pixels** (`dx/dy/r`), magnification-independent (`vis.unscale`, #1013).
- The edited move gets a `provenance` block (per-frame trace, so re-opening restores your work);
  the runtime never reads it.
- **Destination is chosen at the prompt:**
  - **`O`** overwrite **live** → `pycats/characters/data/<cat>.json` (the git-tracked file the sim loads).
  - **`S`** scratch → the editor's gitignored `repros/<cat>-NNNN.json` (auto-incrementing).
  - **`B`** both. **`N`/`Esc`** writes nothing.
- The prompt title reports whether there's a real semantic delta vs an unedited save (#1022/#989),
  and a `SaveError` (uncollapsible window / letter-less box) is caught and written nowhere.

---

## 2. End-to-end walkthrough — authoring one move's boxes

This is the concrete recipe for one move, start to finish. It assumes the editor's editable
install of pycats points at the working tree you intend to commit (see §3, coupling).

**Glossary (used below):** *oracle* = the Python box literal `<cat>_cat.py` (`<STEM>_FIGHTER_DATA`);
*mirror* = the shipped `characters/data/<cat>.json` the sim actually loads; *collapse* = the fold
from per-frame boxes to windowed `Hitbox`es (`pycats/combat/collapse.py`); *provenance* = the
editor's per-frame authoring trace stored inline in the JSON.

1. **Launch** the editor: `.venv/bin/python -m pycats_editor`.
2. **Navigate** to your target: `,`/`.` to the character, `[`/`]` to the move. The terminal
   printout lists the move keys.
3. **Bring in the PM reference GIF.** It auto-resolves per the move→subaction map; press `3` to
   toggle it, `M` for overlay vs side-by-side. For a combo move, step sub-animations with `;`/`'`.
4. **Align and scale to trace.** `PgUp`/`PgDn` (or drag the GIF corner) to match body height;
   `Shift+arrows` / drag / `P` to position. You're matching **motion and box placement scaled to a
   common body height**, not appearance — the #777 GIFs are hurtbox/skeleton renders (#782/#310:
   box *positions are a feel quantity*, which is why this is WYSIWYG and not a datamine import).
5. **Scrub** with `←`/`→` (or click the timeline) to the frame where the box first goes active.
6. **Place the priority box first** (e.g. Narz's tipper, #299/#313), then the base boxes: `A`
   adds a hit box on the current frame; drag its body to position, drag the white ring to size.
   Use `Tab` to cycle boxes, `+`/`-` (Shift ×10) to nudge the focused `dx/dy/r` field precisely.
   > **Note (gap, §4-G8):** the editor has **no author-settable priority/z-order**. Collapse sorts
   > boxes by `(window_start, priority, id)`, but priority isn't exposed in the UI — box order is
   > insertion order. Tipper-first behaviour currently rides on that, not on an explicit control.
7. **Extend the active window** across frames with `Ctrl+←`/`Ctrl+→` (grows the same box/letter
   onto neighbouring frames). For a box that moves, place it per-frame; collapse will store a
   staircase of 1-frame windows (see §4-G3).
8. **Set the note** (`Enter`) to record provenance/citation for the move.
9. **Save** with `S`. **For real authoring, choose `O` (overwrite live)** so the change reaches
   the sim's `characters/data/<cat>.json`; choose `S` (scratch) for experiments you don't want on
   `main`. The prompt tells you whether there's a real geometry delta.
10. **Reconcile the oracle** — the step the editor does *not* do for you, and the campaign's main
    trap. See §3-P1: for any cat with a registered oracle, an editor geometry edit must be mirrored
    into `<cat>_cat.py` by hand (then re-dump), or the drift-guard/flip tests red. Do this before
    running the suite.
11. **Run the guard tests** (from the pycats worktree):
    ```bash
    make test ARGS="-k 'json_flip or drift_guard'"
    ```
12. **Regenerate the JSON mirror** if you edited the oracle in step 10:
    ```bash
    python -m scripts.regen_character_json
    ```
    (Pure re-dump from the oracles; a no-op diff if nothing changed. **Warning:** this overwrites
    `<cat>.json` *from the oracle*, so it will erase an editor-only JSON edit that wasn't mirrored
    into the oracle first — that's exactly why step 10 comes first.)
13. **Regenerate goldens** (box edits are sim-affecting, #768):
    ```bash
    make goldens        # PYCATS_UPDATE_GOLDENS=1 over the 3 golden modules
    ```
14. **Review the regen** per `tests/golden/REGEN_PROTOCOL.md` — read the `.summary.json` sidecar
    diffs (not the blob), confirm the changed hit/KO frames match your intent, and get the
    **author ≠ reviewer** sign-off before close. Post-regen green is circular; the review is the gate.
15. **Full suite + lint, then commit** one move/cat as a unit:
    ```bash
    make test && make lint
    ```
    Commit the JSON mirror + (if touched) the oracle + regenerated goldens together, `Closes #N`.

Run/verify the game itself with `make run` (or an unmerged worktree via
`make run-cmd WHAT=<issue|branch|path>`).

---

## 3. The git-pain playbook

Every way this campaign can redden `main`, with the avoid-pattern for each. **P1 is the big one.**

### P1 — Oracle ↔ mirror drift (the central trap)

**The mechanism.** The runtime loads the **JSON mirror**, not the Python oracle
(`load_fighter_data` returns the JSON branch first; the oracle is *demoted, not deleted* — #881
"O1"). But two tests still pin the mirror to the oracle for every cat with a registered oracle
(`nalio`, `birky`, `narz`, `gnok`, `default`):

- `test_python_json_drift_guard.py` — `assert load_fighter_data(stem) == ORACLES[stem]`.
- `test_<cat>_json_flip.py` — `load_fighter_data("<cat>") == <CAT>_FIGHTER_DATA` **and**
  `json.loads(<cat>.json) == fighter_to_json(<CAT>_FIGHTER_DATA, "<cat>")`.

The editor writes **only** the JSON. So the moment you save a real geometry change to
`nalio.json`, the JSON no longer equals the unchanged `NALIO_FIGHTER_DATA` oracle → **both tests
red.** [inferred from the two assertions above — this is a direct deduction, not yet reproduced by
a live save.]

**The nasty second half:** you cannot fix it by running `regen_character_json`, because that
dumps *from the oracle* and would **overwrite your edit** with the old geometry.

**Avoid-pattern (today).** Mirror the editor's box change into the Python oracle
`<cat>_cat.py` by hand, *then* `python -m scripts.regen_character_json` to produce a byte-matching
JSON. Both tests go green because oracle and mirror now agree. This hand-duplication is the
friction the campaign will hit on every single move — and the reason §4-G1 (retire or auto-write
the oracle) is the top routing question.

### P2 — The classic JSON-flip footgun (reversed here)

The original footgun (documented in `test_python_json_drift_guard.py`'s header, from the #841/#860
gnok incident): change the Python data, forget to regen the JSON, `main` reds. In *this* workflow
the direction is reversed (editor writes JSON, oracle goes stale), but the fix is the same seam —
keep oracle and mirror in lock-step via `regen_character_json`, never hand-edit one alone.

### P3 — Golden regen on sim-affecting edits

Box geometry changes hit/KO timing, so it flips the sim goldens (`test_golden.py`,
`test_golden_summary.py`, `test_screen_parity.py`). Avoid-pattern: `make goldens`, then **review
the `.summary.json` sidecar** and get **author ≠ reviewer** sign-off (`REGEN_PROTOCOL.md`) — a
green suite after regen proves nothing on its own.

### P4 — Render-parity / byte-stability (low risk here)

`test_battle_screen_render.py` guards byte-identical render output. A pure box-geometry edit
reaches paint **only** through the debug hit/hurtbox overlay, which is **default OFF**
(`runtime_settings.show_hitbox_overlay()`). So a box edit generally does **not** flip render
parity — it surfaces in the sim goldens instead (P3). [inferred: no render byte-golden keyed on box
geometry with the overlay off was found.]

### P5 — Fleet merge races

Multiple cats authored in parallel across worktrees can collide on shared files (goldens,
`scripts/`, test lists). Avoid-pattern: **one cat (ideally one move) per branch/commit unit**;
run the full suite right after claiming (fleet merge-race) and merge one cat at a time.

### P6 — Two-repo coupling (#882)

The editor depends on pycats via an **editable install** (`pip install -e ../pycats`), so it
always imports the *working-tree* pycats and its `CHARACTER_DATA_DIR` resolves into the real
checkout. The editor is **not pinned to a released pycats version.** This is precisely why an
`O` (overwrite-live) Save lands on the git-tracked `<cat>.json` on `main` (the #978 finding). Avoid
accidental dirtying: use `S` (scratch) for experiments; keep the editor's editable target pointed
at the worktree you actually intend to commit.

### P7 — Accidental live Save (#978 → #983)

Historically the interactive Save defaulted to the live tracked file with no choice, and several
editor tickets (#964/#972/#976) hand-reverted a dirtied `nalio.json`. That's now mitigated by the
**O/S/B/N destination prompt** (#983) plus the change-delta readout (#1022). Avoid-pattern: read
the prompt; pick `S` unless you mean to author.

### Recommended commit unit + checklist

**Unit:** one cat per branch, ideally one move per commit. **Before close:**

- [ ] Edited move saved to live JSON (`O`), geometry delta confirmed at the prompt.
- [ ] Oracle `<cat>_cat.py` mirrored to match (P1), then `python -m scripts.regen_character_json`.
- [ ] `make test ARGS="-k 'json_flip or drift_guard'"` green.
- [ ] `make goldens` + **sidecar review** + author ≠ reviewer sign-off (P3).
- [ ] `make test && make lint` green.
- [ ] Commit JSON + oracle + goldens together, `Closes #N`.

---

## 4. Gap list (grounded, prioritized)

Each gap: what it blocks, rough size, and whether it maps to an existing slice/issue or needs a
new ticket. **Prereq** = blocks a smooth roster-scale campaign; **QoL** = slows but doesn't block.

| ID | Gap | Blocks | Size | Maps to |
|---|---|---|---|---|
| **G1** | **Editor writes JSON only; oracle stays stale → drift-guard/flip red on every geometry edit** (P1). No round-trip writes `<cat>_cat.py`. | **Prereq** — every move | M (decision + tool) | New ARC/decision (retire vs auto-write oracle); relates to #881 "demote, don't delete" |
| **G2** | **No hurt-box authoring** — can't add a hurt box; hurt is whole-move only. | Prereq **iff** hurtbox placement is in campaign scope | M | #1036 (hurt-box letters/round-trip, OPEN) + a new "add hurt box" editor slice |
| **G3** | Live game consumes **windowed static** boxes; per-frame **motion** is D2-deferred (`scope.md` "Out of scope"). Editor stores a moving box as a staircase of 1-frame windows (over-covers, safe). | Nice-to-have unless a move *needs* smooth motion | L (accept) / XL (engine) | D2 decision (deferred by design); no action for "good-enough" |
| **G4** | No **batch/copy across a frame range** (beyond single-frame extend/dup); no **L/R mirror** helper (facing fixed right). | QoL — slows roster scale | M | New editor (E-side) tickets |
| **G5** | **No playback loop** (MVP bullet unbuilt) — frames only advance on manual scrub. | QoL | S | New editor ticket |
| **G6** | UI polish: **add-hitbox button #1031**, **used-letter indicator #1034**, **text scaling #1012**, **persist zoom #908**. | QoL | S each | Existing OPEN issues (#1031/#1034/#1012/#908) |
| **G7** | **Provenance written only for the edited move**; switching move/character starts a fresh undo history and **drops unsaved edits with no guard**. | QoL — risk of lost work | S–M | New editor ticket ("unsaved-changes guard on switch") |
| **G8** | **No author-settable box priority/z-order** — tipper-first (#299/#313) rides on insertion order, not an explicit control. | QoL — matters for multi-box tippers | S–M | New editor ticket (expose `priority` in inspector) |

---

## 5. Routing (option space — build order NOT decided here)

**Prerequisites for a smooth campaign** (fix before roster-scale authoring):

- **G1 — the oracle/mirror duplication.** This is the one that reds `main` on *every* move, so it
  is the gating question. The option space (pycats-side, an **R**-slice or a decision):
  1. **Retire the oracle** for cats being authored (deregister from both drift-guard `ORACLES`
     maps; JSON mirror becomes the sole truth). Reverses #881's "demote, don't delete."
  2. **Keep the oracle, add an oracle-writer** — the editor (or a pycats tool) also emits the
     `<cat>_cat.py` literal on save, so both stay in sync automatically. Editor-side **E** work +
     pycats serializer.
  3. **Keep hand-duplication** (§3-P1 recipe) — no code, maximal per-move friction.
  → Recommend deciding this **first**, with the human, as an ARC/decision child of #792. It sets
  the whole campaign's per-move cost.

- **G2 — hurt-box authoring**, *if* hurtbox placement is in scope for the campaign. If the campaign
  is hit-box-only for now, G2 drops to nice-to-have. This is Avi's scoping call.

**Nice-to-have** (slow but don't block): G4 (batch/mirror), G5 (loop), G6 (existing QoL issues),
G7 (unsaved-changes guard), G8 (priority control). Mostly **E**-side editor slices; each is its own
DEV, filed one at a time downstream.

**pycats-side (R) vs editor-side (E) split:** G1 is pycats-side (drift-guard/oracle) with an
optional E-side writer; G2 is E-side (add-box) + the existing pycats #1036 round-trip; G3 is a
pycats/engine decision (deferred); G4/G5/G7/G8 are E-side; G6 is a mix of existing E/UI issues.

**Not decided here** (per repo rule — research reports option space, the spec/build order is a
downstream architect/decision ticket with the human): which of G1's three options to take, whether
G2 is in scope, and the order of the nice-to-haves.

---

## Refs

Tracker #792 · ADR-0008 · `docs/pycats-editor-mvp.md` / `-scope.md` (R1–R7 / E0–E8) /
`-data-schema-design.md` · #793 (`docs/research/hitbox-editor-scoping-findings.md`), #782
(position=feel) · save-stamp findings (`docs/research/editor-save-live-data-stamp-findings.md`,
#978→#983) · packaging/coupling #882 · Save/public-name #924 · sim-affecting #768 · open editor
QoL #1031/#1034/#1012/#908, hurt-box #1036 · guards `tests/test_python_json_drift_guard.py` /
`test_<cat>_json_flip.py` / `test_drift_guard.py` · seam `pycats/combat/data.py`
(`load_fighter_data`, `fighter_to_json`, `_fighter_from_json`) / `combat/collapse.py` /
`combat/geometry.py` (`resolve_circle`) / `combat/units.py` (`u`/`vel`, `PX_PER_UNIT`) /
`combat/move_clock.py` / `systems/hit_resolution.py` · regen `scripts/regen_character_json.py` ·
goldens `tests/golden/REGEN_PROTOCOL.md`, `tests/test_golden*.py`, `tests/test_screen_parity.py`,
`tests/test_battle_screen_render.py`.
