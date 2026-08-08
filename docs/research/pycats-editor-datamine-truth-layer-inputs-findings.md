# Editor datamine-truth layer — design inputs (spike findings)

**Ticket:** #1300 (RESEARCH spike, Stage 0 of tracker #1299) · **Agent:** GRAPE · **Date:** 2026-08-07
**Repos read (read-only, no change):** `pycats` (this repo) · `avidrucker/pycats-editor` (sibling)
**Basis:** the #1299 tracker crux + the #1278 prototype + the #1294 origin-gap analysis.

Findings + design inputs only — **no code, no design ruling.** The Stage-1 ARC design consumes this.

---

## TL;DR

- **One px space, confirmed.** The editor draws authored hit/hurt circles by resolving each pycats
  `Circle(dx, dy, r)` against the fighter **rect top-left** — via pycats' own `resolve_circle`
  (`canvas.py:resolve_scene`), then an editor display magnification `vis.scale_resolved` (`VIS_SCALE = 1.5`,
  isotropic) and a separate window-zoom blit. The datamine-truth layer, once feet-anchored by `(w/2, h)`,
  lands in that **same rect-relative px space** and flows through the **same** `resolve_circle → scale → zoom`
  pipeline as authored boxes — so it superimposes directly with no reprojection. The reference GIF stays a
  **separate, independently-scaled backdrop** (`gifcompare.py`), never the alignment basis. The #1299
  hypothesis holds: **a new toggleable layer on the authoring canvas, not a GIF-space overlay.**
- **The anchor belongs at the accept/consume step, not in `propose()`.** The editor applies **no** feet/body
  anchor of its own to authored boxes (rect-top-left origin, verified — see Q2). The datamine candidate
  arrives from `_circle_from_world` in an **un-anchored** propose()-space (`dy = -u(y)` from the world
  origin). Adding `(w/2, h)` at the point the editor turns a candidate into a drawable box lands it in the
  editor's own space with **no double-count**. This matches #1294's "where should the anchor live" being the
  accept step.
- **Cross-repo mechanism is already decided (ADR-0008 / ADR-0022): the editor reads pycats LIVE via an
  editable install** (`pip install -e ../pycats`; pycats is *not* in the editor's `[project].dependencies`).
  So the datamine layer imports `pycats.combat.datamine_proposer` the same way it already imports
  `load_fighter_data` / `resolve_circle`. **One wrinkle:** the datamine **fixtures** it must consume live
  under `pycats/tests/fixtures/datamine/`, which the `include = ["pycats*"]` package does **not** ship (and
  which do not exist in the editor repo at all). The seam is importable; its inputs are not packaged.
  Resolving that is the one true cross-repo data-flow decision the ARC must make (Q3).
- **The `+1` frame mapping is unowned code today.** `MoveClock = datamine idx + 1` is verified (the #1278
  prototype) but `propose_per_frame` explicitly does NOT apply it — it is "the editor/accept step's job
  (#1220)". #1220 (ghost-box + accept) is **OPEN / not shipped** (confirmed absent from the editor: no
  datamine/propose/ghost/accept/candidate code or fixtures anywhere in `pycats-editor`). The datamine-truth
  *review* layer this tracker adds needs the same mapping; it should share one implementation with #1220's
  accept, not fork a second copy.

---

## Q1 — How does pycats-editor render today, and where would a datamine layer plug in?

**The editor is Python + pygame-ce**, `src/pycats_editor/` (ADR-0008; audited in
`docs/research/pycats-editor-implementation-audit-findings.md`, #1121). It is NOT a web/React app (the
`pycats-editor-react-rewrite-findings.md` doc is a *proposal*, not shipped).

Render surfaces:

- **Authoring canvas** (`canvas.py:resolve_scene`; `test_e1_canvas` #891): draws the fighter body + its
  hit/hurt **circles** for the current frame. The Circle→screen transform is a two-stage composition (Q2).
- **Frame timeline + scrub** (`test_e2_timeline` #901): the current frame drives which box set is shown.
  Frames step by ←/→ or timeline click — **no play/pause auto-advance** (the audit's biggest gap).
- **Inspector** (`test_e3_inspector` #909): select a box, edit geometry/scalars/timing.
- **Per-frame authoring + stable ids** (`test_e4_per_frame` #913) with reverse-collapse restore.
- **GIF compare** (`gifcompare.py`, on-disk slice E9 / #976): decode the reference Mario GIF (Pillow),
  toggle hit/hurt/GIF layers independently (keys 1/2/3), draw fighter OVER (trace) or BESIDE (compare) the
  GIF (key M), and zoom/pan the GIF **view-only** (never saved).
- **Layer-toggle machinery already exists** — `Layers` + `toggle_layer` + `filtered_scene` in `gifcompare.py`
  drop hidden-layer circles from the resolved scene. A datamine layer is a natural fourth flag alongside
  hit/hurt/gif.

**Where a datamine-truth layer plugs in:** a **new toggleable layer on the authoring canvas** (the canvas that
draws authored circles), gated by a new flag in the existing `Layers` / `toggle_layer` machinery — **not** a
GIF-space overlay and **not** a separate panel. It reuses the canvas's existing `resolve_circle → scale → zoom`
transform; it does not touch the GIF view transform.

## Q2 — One px space or two?

**One.** The editor's authored-box transform is a two-stage composition:

- **Stage A — anchor (pycats, reused verbatim):** `canvas.py:resolve_scene` calls pycats
  `combat/geometry.py::resolve_circle(circle, origin_x, origin_y, facing_right, width)`. `dx/dy` are offsets
  from the fighter **rect top-left**: `cx = origin_x + dx` (facing right) / `origin_x + width - dx`
  (facing left, mirrored around body centre); `cy = origin_y + dy`. The editor's own canvas header states it:
  *"`Circle(dx, dy, r)` are px offsets from the fighter's top-left origin … the editor works in px directly —
  no unit scaling."* Body origin = the `stand_size or PLAYER_SIZE` rect centred in the base surface
  (`__main__.py:_scaled_body_origin`).
- **Stage B — display magnification (editor):** `vis.py::scale_resolved(resolved, origin, k=VIS_SCALE)` with
  `VIS_SCALE = 1.5`, isotropic about the origin (`ox + (cx-ox)*k`, `r*k`); same helper for draw AND hit-test.
  A further whole-surface window zoom (`zoom.py` `PRESETS = (1.0, 1.5, 2.0)`) blits the base surface to the
  window. **No `units.u` factor is applied in the editor** — Circle px are used directly; pycats'
  `PX_PER_UNIT ≈ 5.4` lives upstream, only where pycats builds Circles from units.

Datamine candidates come from `datamine_proposer._circle_from_world(z, y, size)` →
`Circle(dx=u(z), dy=-u(y), r=u(size))` with **no origin translation** — propose()-space pins the datamine
world origin (feet-centre) onto pycats' rect-top-left. Anchoring by the fighter feet-centre `(w/2, h)` (rect
midbottom, from `stand_size or config.PLAYER_SIZE`) re-expresses the datamine box in the **same
rect-top-left-relative frame** authored boxes already use — after which it resolves through the very same
`resolve_circle` (facing mirror included; the dump is facing-right like pycats) and the same Stage-B scale.

So authored + anchored-datamine are **the same coordinate space**, and both are **independent of the GIF's
view transform**: the GIF is scaled/panned on its own `GifView` and blitted as a backdrop OVER/BESIDE
(`gifcompare.py::gif_dest`); the authored circles come from `filtered_scene`, which applies **no** GIF
scale/offset. In OVERLAY mode the GIF and boxes share only the `origin` anchor — the boxes are never
reprojected into GIF space. The datamine layer superimposes on the authored layer with no GIF alignment.

**Anchor self-consistency:** the `(w/2, h)` anchor reads `stand_size or PLAYER_SIZE` — the exact source the
editor already uses for its on-screen body rect (`canvas.py:body_size`). So the anchor lines up with the
editor's own body placement by construction.

**Double-count check:** the editor applies **no** feet/body anchor of its own to authored boxes (origin = the
fighter rect top-left it places on the canvas; confirmed by reading the draw + hit-test path). Applying
`(w/2, h)` to the datamine layer at the accept/consume step is therefore correct and does not stack on any
existing anchor.

## Q3 — What crosses the repo boundary, and how?

**What the editor must consume from pycats:**

| Input | Where | Reachable via editable install? |
|---|---|---|
| `datamine_proposer.propose_per_frame` / `_circle_from_world` | `pycats/combat/datamine_proposer.py` | **Yes** (in `pycats*`) |
| feet-centre anchor `(w/2, h)` from `stand_size or config.PLAYER_SIZE` | `pycats/config.py` + fighter data | **Yes** |
| `resolve_circle` (shared draw seam) | `pycats/combat/geometry.py` | **Yes** (already imported) |
| `MoveClock = datamine idx + 1` frame mapping | *unwritten* — prototype-only; #1220's job | **N/A — code doesn't exist yet** |
| datamine **fixtures** `mario_*_hitboxes.json` | `pycats/tests/fixtures/datamine/` | **NO — `tests/` is not in `include=["pycats*"]`** |

**Mechanism — already ruled, don't re-open:** ADR-0008 + ADR-0022 (owner ruling on #1281, CLOSED) establish
that **the editor reads pycats live via an editable install** (`pip install -e ../pycats`; pycats is absent
from the editor's `[project].dependencies`, which lists only `pygame-ce`, `Pillow`). This was ruled Option A
over pinning a pycats SHA. Surface drift is caught by a pycats-side approval test over the `(cat, move_key)`
surface, whose failure message points at the editor census as the consumer to update. pycats never imports
editor code. **So the datamine layer needs no new dependency mechanism** — it imports `datamine_proposer`
exactly as the editor already imports `load_fighter_data`.

**The one open data-flow decision (ARC must decide):** the datamine **fixtures** are test artifacts under
`pycats/tests/`, which the editable install does not expose (and which do not exist in the editor repo).
Options to weigh (not decided here):

1. **Promote fixtures into the package** — e.g. `pycats/combat/datamine_fixtures/*.json` as package data — so
   import-time access matches the seam that reads them. Cleanest for the editor; changes where fixtures live,
   and pulls test artifacts into shipped package data.
2. **Point the editor at the pycats checkout path** — the editable install already implies a source checkout
   is present; the editor resolves `<pycats_root>/tests/fixtures/datamine/`. Zero pycats change, but couples
   the editor to pycats' repo *layout* (fragile — a fixtures move breaks it with no ADR-0022-style guard).
3. **The editor dumps its own datamine at author time** (run `scripts/datamine_hitboxes.sh` per subaction)
   rather than consuming committed fixtures — decouples entirely, but adds a brawllib-rs toolchain dependency
   to the editor.

This is the concrete thing the Stage-1 ARC must settle; it interlocks with, but is narrower than, the
now-closed #1281 — that guarded the move-key surface; this guards/relocates the **fixture** surface.

## Q4 — Consumed #1294 findings (origin anchor + residual position-scale)

#1294 (RESEARCH, still OPEN) analysed the datamine→px gap while building the #1278 viewer. The facts the
editor layer should **reuse, not re-derive**:

- **The gap is two independent parts.** (a) A missing **feet-centre origin anchor** (vertical, dominant):
  `_circle_from_world` maps Brawl's feet-centre world origin straight onto pycats' rect-top-left, so a raw
  candidate floats ~a body-height (≈50–60px) too high. Anchoring by `(w/2, h)` lands `dy` in the authored
  band across all four nalio fixtures (the tell: dsmash, a LOW move, renders raw *above the head* — a pure
  origin artifact). (b) A residual **forward position-scale over-projection** (horizontal, ~20–50px more
  forward than authored after anchoring), consistent with `u()` — a playtest-chosen **radius** factor —
  mis-serving as a **position** scale (#120/#195: there is no fixed world→px position scale).
- **Design consequence for the layer:** apply part (a) — the `(w/2, h)` anchor — so the eyeballed overlay is
  vertically correct, and **surface part (b) as-is** (the remaining forward offset is the informative signal a
  human reads / nudges, exactly what the #1278 `o`-toggle shows). The layer is a *review/visualisation*
  surface; it must not covertly "correct" (b), which has no grounded scale factor yet.
- **Radii are exact.** Authored radius `== u(datamine size)` to the pixel on every nalio box — the datamine
  layer's circle sizes already match authored, so only *position* is in question.

#1294 remains the ticket that will *confirm & quantify* (b) and rule where the anchor lives in production
`propose()`; this layer consumes its display-side finding (anchor at the editor step) without pre-empting that
ruling.

## Rough UX sketch (which #1278 toggles carry over)

The #1278 prototype keys map onto the editor's existing layer/scrub model:

| #1278 key | Purpose | In-editor form |
|---|---|---|
| `d` datamine layer | show/hide datamine truth boxes | **new flag in `Layers` / `toggle_layer`** (joins hit/hurt/gif 1/2/3) |
| `a` authored layer | show/hide authored boxes | already the editor's authored draw (existing hit/hurt toggles) |
| `b` body | show/hide standing hurtbox context | already drawn by the editor canvas |
| `o` feet-centre anchor | toggle the `(w/2, h)` anchor | **keep as a debug toggle** — anchor ON by default (correct overlay); OFF reveals the raw propose()-space gap (#1294 part b) for the author |
| ←/→ step · space play/pause | per-frame stepping | reuse the editor's frame scrub; play/pause is an editor gap (audit), not owned here |

Per-frame stepping ties to the **editor's own frame clock** (MoveClock), with the datamine layer indexed by
`datamine idx = MoveClock − 1`.

## Open questions for the Stage-1 ARC (design decisions, not settled here)

1. **Fixture data-flow (Q3):** promote fixtures to package data, point at the checkout, or editor-side dump?
   (The one true cross-repo decision.)
2. **Who owns `MoveClock = datamine idx + 1`?** It must be shared with #1220's accept step, not duplicated —
   does #1220 land the mapping first, with this layer consuming it, or vice-versa? (Sequencing vs #1220.)
3. **Anchor site in the editor:** a shared `datamine_candidate → drawable` helper that applies `(w/2, h)` +
   the frame mapping, reused by both the review layer and #1220's accept? (Avoids two anchor copies.)
4. **Does the review layer read committed fixtures, live `propose_per_frame` output, or both?** (Ties to Q3.)
5. **Scope vs #1220:** #1220 draws datamine candidates as *ghosts to accept*; this tracker draws datamine as a
   *review-truth layer*. Are these the **same draw path** at different opacities/intents, or two? (Likely one
   draw path, two intents — the ARC should collapse them if so.)

## Refs

- Prototype: `scripts/datamine_hitbox_qa_viewer.py` (#1278, on main) — `datamine_layer`, `feet_centre_anchor`,
  `authored_boxes`, `make_transform`.
- pycats seams: `pycats/combat/datamine_proposer.py::_circle_from_world` / `propose_per_frame`;
  `pycats/combat/geometry.py::resolve_circle`; `pycats/config.py::PLAYER_SIZE`; `pycats/combat/units.py::u`.
- Editor: `avidrucker/pycats-editor` `src/pycats_editor/{canvas,vis,zoom,gifcompare,__main__,working}.py`;
  audit `docs/research/pycats-editor-implementation-audit-findings.md` (#1121). Editor transform:
  `canvas.py:resolve_scene` (reuses pycats `resolve_circle`) → `vis.py:scale_resolved` (`VIS_SCALE = 1.5`) →
  `zoom.py` window blit. Datamine/propose/ghost/accept: absent (confirmed by grep across the editor repo).
- Decisions: ADR-0008 (editor reuses pycats live via editable install) · ADR-0022 / #1281 CLOSED (move-key
  surface guard; editable install over SHA-pin) · ADR-0011 / #962 (`units.u` seam) · #120/#195 (no fixed
  world→px position scale).
- Tracker #1299 · origin-gap research #1294 · editor ghost-box/accept #1220 (OPEN) · placement sub-tracker
  #1206 · editor tracker #792.
