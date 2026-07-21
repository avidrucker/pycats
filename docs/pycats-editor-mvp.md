# pycats-editor — MVP feature list & design decisions

**Status:** decisions ratified by the game-designer (interactive grill/guide session, 2026-07-20);
design not yet started. **Tracker:** #792. **Research basis:** #793 findings doc
[`docs/research/hitbox-editor-scoping-findings.md`](./research/hitbox-editor-scoping-findings.md)
and the model findings #782 [`docs/research/pm-hit-hurtbox-model-findings.md`](./research/pm-hit-hurtbox-model-findings.md).

> **This doc is the handoff surface for `pycats-editor`.** It records *what the tool is* and
> *the decisions already made*, so a fresh agent can pick up at the design step without re-deriving.
> The formal ADR is **`docs/adr/0008-*`** (pending — see "What's left", below).

---

## What `pycats-editor` is

A **separate sister project** (its own repo, created when the first build slice starts) built in
**pygame-ce**, importing/reusing pycats modules (render, `resolve_circle`, fighter data). Its job:

- **Inspect / view** animations + hit/hurtboxes for **both** pycats fighters **and** the Project M
  reference GIFs (the #777 set, indexed by [`docs/pm-reference/mario-gif-index.md`](./pm-reference/mario-gif-index.md)).
- **Modify** pycats hit/hurtboxes — **per frame** — and save them back as data pycats can load.

It exists because hand-authoring box **positions** at the scale of "compare every Mario animation
against every Nalio move" is too slow (the #782 finding: box *scalars* datamine exactly, but
*positions* are a feel quantity — a WYSIWYG editor is the practical way to place them).

## MVP feature list (game-designer's words)

Per move / animation / attack:

- **Edit hit + hurt boxes per frame** — manually update the boxes for each frame.
- **Scrub** back and forth through frames.
- **Loop** playback of the animation.
- **Toggle** the hitbox / hurtbox display on and off.
- **Overlay** the pycats cat fighter over the PM reference GIFs.
- **Scale up/down and translate the GIF** — view it **beside** the fighter, or **directly behind**
  it to **trace** boxes onto the fighter as needed.

## Design decisions (D0–D6)

| # | Decision | Consequence |
|---|---|---|
| **D0** | **Fold #778 entirely into the editor.** | #778 (side-by-side sandbox) is redundant → close as superseded by #792; its compare view becomes part of pycats-editor. |
| **D1** | **Separate sister project `pycats-editor`, in pygame-ce, reusing pycats modules.** | Gets the real game render for free (no second renderer to drift); editor-only deps stay out of pycats' manifest. |
| **D2** | **Per-frame authoring** (hit + hurt, each frame) + per-frame side-by-side viewing. | The editor stores per-frame box data. **The live *game* consuming per-frame boxes is a separate, deferred decision** — the editor is not blocked on it, and viewing/authoring per-frame needs no main-engine change. |
| **D3** | **Box data → per-fighter JSON files** (editor writes; pycats loads via an extended `load_fighter_data`). | Stdlib `json`, no new dep, both programs share it, holds per-frame keyed boxes. Provenance/citations move to a `notes` field or sidecar. Migrating today's static `.py` literals → JSON is its own slice. |
| **D4** | **pygame_gui** for editor chrome (scrubber slider, dx/dy/r fields, file dialogs). | Editor-only dep (MIT, maintained); removes hand-rolled-widget cost. |
| **D5** | **Pillow** for GIF frame decode. | Editor-only dep; ergonomic per-frame extraction + `.resize()` for the scale/translate/trace feature. |
| **D6** | **Design-first**: #792 stays the tracker in pycats; next child = a DESIGN doc; create the `pycats-editor` repo when the first build slice starts. | No empty repo; decisions/design stay discoverable in pycats until code exists. |

## Key constraints to respect (from the research)

- **Determinism / goldens (#768):** a box's `dx/dy/r` feed `resolve_circle` → hit resolution → the
  `sim/runner.py snapshot()` golden digest. Editing box data is **sim-affecting**. Safe pattern is
  **edit → serialize (JSON) → reload → replay** (a new frozen `FighterData` per match); **never
  live-mutate a running match** (frozen dataclasses forbid it and it breaks determinism). The editor
  is a separate program, so it only perturbs pycats goldens once pycats *loads* the changed JSON — a
  reviewed golden regen at that point.
- **pycats has no box-data write path today** — data is hand-written frozen-dataclass Python literals
  loaded by an import switch (`pycats/combat/data.py load_fighter_data`). The editor + the JSON schema
  introduce the first serializer.
- **Reusable pycats assets:** `render_hitbox_overlay` + `resolve_circle` + `_active_hurtbox`
  (`pycats/render_battle.py`, `pycats/combat/geometry.py`) already draw/resolve the boxes; the
  editor imports these rather than re-implementing.
- **Reference is motion, not skin:** the #777 GIFs are hurtbox-capsule/skeleton renders — compare
  motion + box placement, scaled to a common body height, not appearance.

## Progress (what's done) + what's left

**Done (2026-07-20):**
1. **ADR `docs/adr/0008-pycats-editor-...md`** written (D0–D6 + MVP list).
2. **#793** (research child) closed — findings + this doc + ADR on main.
3. **#778** closed as superseded (folded into the editor per D0).
4. **Ruling** posted on #792 (D0–D6 table).
5. **DESIGN child #809** filed, then designed →
   **[`docs/pycats-editor-data-schema-design.md`](./pycats-editor-data-schema-design.md)**. That doc
   is the spine: JSON box-data schema (thin static mirror + inline `provenance` + drift-guard test),
   the `load_fighter_data` seam, the px↔`Circle(dx,dy,r)` mapping, and the editor screens/interactions.
   Chosen storage architecture: **A + drift-guard** (candidates A/B/C compared in §0 of that doc).

**What's left (next children, one-at-a-time downstream of #809):**

- **SCOPE** — cut the design into tracer-bullet DEV slices (data dir + loader JSON branch +
  migration; the `MoveData.hurtbox` override; the editor's canvas/timeline/inspector; GIF overlay).
  Open items to settle there are in §5 of the design doc.
- **DEV slices** — build incrementally, TDD, each slice green with a regression test; goldens stay
  green throughout.

## References

#792 (tracker) · #793 (this research child) · #782 (hit/hurtbox model + authoring-path analysis) ·
#778 (folded in) · #777 (Mario GIF set + manifest) · #768 (box moves are sim-affecting) · #310
(position = feel) · #309 (`zone_dy`). Code: `pycats/combat/data.py`, `pycats/combat/geometry.py`,
`pycats/render_battle.py`, `pycats/sim/runner.py`, `pycats/screen_manager.py`.
