# Editor batch/copy + L/R mirror (G4) — scoping findings

**Ticket:** #1182 (RESEARCH, `combat:editor`, child of #792) · from #1072 §4-G4 / §5 and the
#1078 Q3 nice-to-have order (G4 is the last, after G7 / #1012 / G8, all closed).
**Produces:** this findings doc + an option space. No editor/pycats code lands here; a downstream
architect/decision (ARC) + DEV slice(s) implement the pick.

G4 bundles **two independent** editor QoL helpers (findings §4-G4): *batch/copy across a frame
range* and an *L/R mirror* helper. They share nothing but the "speeds roster-scale authoring, blocks
nothing" motivation, so they are scoped separately below and §5 recommends whether they are one DEV
slice or two.

All code claims are quoted from `pycats-editor` HEAD and `pycats` HEAD (worktree
`wt-fig-pycats-1182`), not the spec.

---

## 1. Current copy/extend surface (what exists, where it stops)

Two primitives exist today; both are **single-frame**.

| Helper | Key | Function | Behavior (verbatim from the source) |
|---|---|---|---|
| **Duplicate** | `D` | `working.py::dup_box` | Clones the selected box under a **new id**, offset `+DUP_OFFSET` (15px) right/down. "A hit clone lands on `frame` only; a hurt clone is whole-move." A hit clone gets a **new letter** (`assign_hit_letter`) — it is a new box, not a window extension. |
| **Extend window** | `Shift+←` / `Shift+→` | `working.py::extend_box` | Grows a hit box's active window from `frame` onto its **immediate neighbour** (`direction` ±1), "copying this frame's geometry + scalars under the SAME id (#1055)… No new letter is minted — the box keeps its id and letter (#1030)." One neighbour frame per press; no-op if the box already spans it or the neighbour is outside `startup+active+recovery`. |

**Where it stops (the G4 gap):**
- `extend_box` copies **one box** onto **one adjacent frame** per invocation. Extending a box across
  a 6-frame active window is 5 discrete `Shift+→` presses; there is no "extend to end of active" or
  "copy onto frames N..M".
- `dup_box` copies **one box** onto **the current frame only**. There is no "copy this box's geometry
  onto a frame range" and no "copy this frame's **whole box set** onto another range".
- There is **no mirror**: authoring is facing-fixed-right (see §3). A physically left-facing or
  bilaterally-symmetric move is redrawn by hand.

---

## 2. Batch/copy — option space + the forks a human must settle

The mechanic is "extend the reach of `extend_box`/`dup_box` from single-frame to a frame range." Three
design forks hide inside it; none is decidable from the code alone.

### Fork 2a — Copy unit
- **Option A — one selected box across a range.** The natural generalization of `extend_box`: pick a
  box, name a target range, replicate its row on each frame. Smallest build; covers the common
  "this hitbox is active frames 3–8" case in one action.
- **Option B — a whole frame's box set onto a range.** Copy *every* box on frame N onto frames M..K.
  Covers "the whole active window looks like frame 3." Larger; needs a per-target-frame merge policy
  (overwrite? skip boxes already present, as `extend_box` does?).
- Recommend **A** as the v1; B is a strict superset that can follow if demand appears.

### Fork 2b — Range input (author ergonomics)
- **Option A — directional "extend to bound"** (`Shift+Ctrl+→` = extend to end of active, etc.). Reuses
  the `extend_box` mental model and its neighbour-clamp (`1 … startup+active+recovery`); no new UI.
- **Option B — explicit from/to frame entry** (type a range). More flexible, needs a text-input mode
  the editor does not have for this.
- **Option C — multi-select frames on the timeline**, then copy. Most flexible, largest (timeline
  multi-select is not built).
- Recommend **A** — it is the lowest-friction increment over today's keys.

### Fork 2c — id / letter / provenance semantics (the correctness fork)
`extend_box` and `dup_box` already diverge here, so a batch copy must pick a lane explicitly:
- **Window-extend semantics** (like `extend_box`): the copied rows share the source's **id and
  letter**; the box's *window* grows. This is what "this hitbox is active frames 3–8" means, and it is
  the behavior the #1176 priority model assumes (id = priority rank, letter = identity, carried across
  the window).
- **New-box semantics** (like `dup_box`): each copy is a fresh id + fresh letter — a *different* box
  that happens to share geometry.
- These are not interchangeable: a batch copy that mints new ids per frame would create N one-frame
  boxes where the author meant one N-frame box, inflating the letter set and the provenance rows, and
  breaking the #1176 assumption that a box's id is stable across its window.
- Recommend the batch copy default to **window-extend semantics** (shared id/letter) — it matches the
  dominant use case and the reorder model; `dup_box`'s new-box path stays the single-frame `D`.

**Primary refs:** `working.py::extend_box` (SAME id, #1055/#1030), `dup_box` (new id + `assign_hit_letter`),
`DUP_OFFSET = 15`; #1176 (id/letter/provenance model), #1029/#1030 (stable letters).

---

## 3. L/R mirror — option space + the forks a human must settle

### The pivotal finding: the runtime already mirrors facing
Boxes are authored **facing-right-relative**; the sim applies the L/R flip at resolve time. From
`pycats/combat/geometry.py::resolve_circle` (verbatim):

> `dx`/`dy` are offsets from the fighter's top-left origin in facing-RIGHT-relative coordinates. When
> the fighter faces left the offset is mirrored **around the body centre** (not the left-edge origin):
> `facing right: cx = origin_x + dx` / `facing left: cx = origin_x + width - dx`
> so a symmetric body part (`dx == width/2`) is facing-invariant… and an attack pokes out the side it
> faces.

The editor's own `canvas.py` documents the same: "facing left mirrors x around the body centre (#64)",
and `resolve_working_scene` resolves through the identical `resolve_circle` with a `facing_right` flag.

**Consequence:** a left-facing move is **already correct** from right-authored boxes — the engine does
the mirror every frame. An editor "L/R mirror" is therefore a **convenience, not a correctness need**.
That reframes what the helper is *for*, which is the first thing the ARC must rule on:

- **Purpose A — symmetric-move authoring:** emit a mirrored *copy* of a box/move so a bilaterally
  symmetric attack (both sides hit) is authored once. This is the only purpose that adds boxes the
  engine's runtime-flip does **not** already produce.
- **Purpose B — author a physically *asymmetric* left variant:** rare; a move whose left-facing shape
  differs from its right-facing shape. pycats has no per-facing box model today (one right-relative
  set, engine-flipped), so this would imply a **schema/model change** — flag as out of the E-side G4
  scope.
- **Purpose C — a preview toggle:** flip the *view* to sanity-check how the move reads facing left,
  purely non-destructive (no boxes added). Cheapest; adds no data.

Recommend the ARC treat **A** (symmetric copy) as the batch-copy sibling and **C** (preview) as a
trivial view aid; **B** is a different (cross-repo) feature and should be declined for G4.

### If Purpose A (symmetric copy) is chosen — its sub-forks
- **Axis + math:** mirror `dx` about the body centre — `dx → width - dx` (the `resolve_circle`
  convention), `dy`/`r` unchanged. Confirm `width`/body-centre source (`canvas.py::_body_width`).
- **Scope:** hit boxes only, or hurt too? (Hurt boxes are whole-move and usually already symmetric —
  probably out of scope.) One box, current frame, or whole move?
- **Copy vs transform:** emit a mirrored *copy alongside* the original (symmetric = both sides), vs
  transform in place (asymmetric — but that is Purpose B). For symmetric authoring the answer is copy.
- **Identity:** a mirrored copy is a **new box** → new id + new letter (matches `dup_box`), because it
  is a distinct box that also hits, not a window extension of the original.

**Primary refs:** `pycats/combat/geometry.py::resolve_circle` (the facing-flip math),
`pycats-editor/canvas.py` (#64 mirror note, `_body_width`, `resolve_scene`),
`working.py::resolve_working_scene` (`facing_right` flag).

---

## 4. E-side vs pycats-side split

- **Batch/copy (§2):** fully **E-side**. It composes existing `working.py` primitives over a frame
  range; no pycats change.
- **L/R mirror (§3):** **E-side** for Purpose A (symmetric copy) and C (preview) — both operate on the
  right-relative `WorkingMove` and reuse the existing `facing_right` resolve path. Purpose B
  (per-facing asymmetric geometry) would be **cross-repo** (pycats needs a per-facing box model it does
  not have) — that is why B is recommended out of scope for G4. This confirms findings §5's "G4 is
  E-side" label, with the one caveat that B, if ever wanted, is not.

---

## 5. Recommendation

1. **Scope G4 to E-side only.** Batch/copy and the mirror-as-symmetric-copy / mirror-preview are all
   editor-side; decline the asymmetric-per-facing variant (Purpose B) as a separate cross-repo feature
   outside G4.
2. **File as two DEV slices, not one.** Batch/copy (§2) and L/R mirror (§3) are independent — different
   code paths, different forks, no shared state. Bundling them into one ticket would violate the
   single-deliverable rule and couple two reviews. Recommend the ARC ratify a small spec for each:
   - **DEV-a — batch/copy:** copy-unit = one box (Fork 2a-A), range = directional extend-to-bound
     (Fork 2b-A), semantics = window-extend / shared id+letter (Fork 2c).
   - **DEV-b — L/R mirror:** symmetric copy (Purpose A) + optional preview toggle (Purpose C); mirror
     `dx → width - dx`, hit-only, new-box identity; explicitly not per-facing geometry (Purpose B).
3. **Order:** batch/copy first (higher daily payoff, no facing subtlety), mirror second.

The build order and the spec picks themselves are a **downstream ARC/decision ticket with the human**
(repo rule — research reports option space only). This doc settles the option space and the forks; it
does not decide them.

---

## Refs

#1072 (§4-G4, §5) · #1078 (Q3 order) · #792 (tracker) · #1176 (box priority reorder — id/letter/
provenance model) · #1029 / #1030 (stable letters) · #1055 (extend keeps id) · #1036 (hurt-box
round-trip) · #64 (body-centre mirror) · `pycats/combat/geometry.py::resolve_circle` (facing-flip
math) · `pycats-editor` `working.py` (`extend_box`, `dup_box`, `DUP_OFFSET`, `resolve_working_scene`),
`canvas.py` (`_body_width`, `resolve_scene`, #64 note), `keybindings.py` (`D`, `Shift+←/→`).
