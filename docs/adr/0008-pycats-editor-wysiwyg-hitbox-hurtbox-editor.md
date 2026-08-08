# ADR-0008 — pycats-editor: a sibling pygame-ce WYSIWYG hit/hurtbox editor

- **Status:** Accepted
- **Date:** 2026-07-20

## Context

Authoring pycats fighters' hit/hurtbox **positions** by hand is slow, and the goal (#792)
is to compare **every** Mario animation against **every** Nalio move for matching duration
and box placement — a very high volume of circle placements. Research established the model
and the option space:

- **#782** (`docs/research/pm-hit-hurtbox-model-findings.md`): PM/Brawl combat *scalars*
  datamine exactly, but box *positions* are a feel quantity (no skeleton, no fixed unit→px
  scale — #310). A WYSIWYG editor is the practical tool for the positional layer.
- **#793** (`docs/research/hitbox-editor-scoping-findings.md`): pycats already has the
  "visualize half" (`render_hitbox_overlay` + `resolve_circle`), but box data is hand-written
  frozen-dataclass Python literals with **no write path**; edits are sim-affecting (#768), so
  the safe pattern is edit → serialize → reload → replay, never live-mutation. Option space:
  (A) in-game overlay, (B) standalone side-program, (C) adapt an existing tool (C collapses —
  no adaptable tool exists).

The game-designer walked the decision tree interactively (grill / guide-human-decision session,
2026-07-20) and ratified the choices below. The canonical spec + MVP feature list live in
`docs/pycats-editor-mvp.md`.

## Decision

We will build **`pycats-editor`**, a **separate sister project written in pygame-ce** that
imports/reuses pycats modules (render, `resolve_circle`, fighter data). Its purpose: **view**
animations + hit/hurtboxes for both pycats fighters and the Project M reference GIFs (#777),
and **edit pycats hit/hurtboxes per frame**. Specifically:

- **D0** — Fold **#778** (side-by-side sandbox) entirely into the editor; #778 is superseded by #792.
- **D1** — Separate sister project in **pygame-ce**, reusing pycats modules (not a foreign GUI
  toolkit) — so it gets the real game render without a second renderer, and keeps its own deps
  out of pycats' game manifest.
- **D2** — **Per-frame authoring** of hit + hurt boxes, with per-frame side-by-side viewing. The
  live *game* consuming per-frame box data is a **separate, deferred** decision; the editor is not
  blocked on it (authoring/viewing per-frame needs no main-engine change).
- **D3** — Box data lives in **per-fighter JSON files** (editor writes; pycats loads via an
  extended `load_fighter_data`); provenance/citations move to a `notes` field or sidecar.
- **D4** — **pygame_gui** for editor chrome (scrubber, numeric fields, dialogs) — an editor-only dep.
- **D5** — **Pillow** for reference-GIF frame decode — an editor-only dep.
- **D6** — **Design-first**: #792 stays the tracker in the pycats repo; the next child is a DESIGN
  doc; the `pycats-editor` repo is created when the first build slice starts.

## Consequences

**Easier / enabled:**
- The editor reuses pycats' actual render + box resolution, so what you edit matches the game
  (true WYSIWYG) without maintaining a second renderer.
- Editor-only dependencies (`pygame_gui`, `Pillow`) never touch pycats' game manifest.
- A shared JSON box-data format gives pycats its first serializer and makes box data
  diff-reviewable; both programs read/write it.

**Harder / follow-on work:**
- pycats gains a JSON load path in `load_fighter_data`, and the existing static Python-literal
  box data must be **migrated to JSON** (its own slice); the provenance comments need a home
  (`notes`/sidecar).
- Box edits remain **sim-affecting** (#768): once pycats loads changed JSON, that fighter's
  goldens need a reviewed regen. The editor perturbs nothing until the game loads its output.
- Per-frame authoring produces data richer than today's static-per-move model; **whether/when the
  live game consumes per-frame boxes is deferred** and ties to the #782 interpolation/swept-capsule
  gap.

**Ruled out:**
- A standalone editor in a foreign GUI toolkit (tkinter / Dear PyGui / PySide6) — rejected in favour
  of staying in pygame-ce and reusing pycats.
- A separate read-only #778 sandbox as its own deliverable — folded into the editor.
- Live in-match mutation of box data — forbidden (frozen dataclasses + determinism/goldens).

**Follow-on tickets (filed one-at-a-time downstream of #793):** the DESIGN child (JSON schema +
editor screens/interactions), then decomposed build slices under #792.
