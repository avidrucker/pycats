# pycats-react-editor — build handoff

> **Agent:** BANANA · **Authored:** 2026-08-07 · **Ticket:** #1307

Handoff for the agent (or human) who builds **`pycats-react-editor`**, the web rewrite of the
box editor ratified in #1307 (downstream of the #1235 research). This doc is the builder's
brief: what was decided, why, the verified facts you must not re-litigate, and the contract
the new editor has to honor. Read it before writing code.

## The one-paragraph summary

Build a **new, additive** web editor — a sibling repo `pycats-react-editor` — that authors the
same hitbox/hurtbox box data the current pygame editor produces. The existing `pycats-editor`
(pygame-ce) stays the maintained primary and is **not** retired. The web editor is a **full
React rewrite** using a **TypeScript reimplementation** of the small combat-geometry contract
(fidelity path A), rendered as an **SVG + Canvas 2D hybrid**. It is a go-now decision, not
gated on any product-direction change.

## The rulings (from #1307)

| Q | Decision | Notes |
|---|----------|-------|
| **Q1 — Direction** | Keep `pycats-editor` (pygame) **+** new sibling `pycats-react-editor` (full React rewrite) | Two editors coexist; pygame stays primary. The React app is additive. |
| **Q2 — Fidelity path** | **A — TypeScript reimplementation** of geometry/collapse/serialize | Chosen over Pyodide (C) and a Python backend (B). See "Why A is safe here" — the risk is far lower than the #1235 findings first framed. |
| **Q3 — Rendering** | **SVG + Canvas 2D hybrid** | SVG `<circle>` per box (drag/hover/select + test targeting); Canvas 2D underlay for the reference GIF frame. WebGL declined — unjustified at this scene size. |
| **Q4 — Trigger** | **Go now**, on its own merits | Not gated on opening authoring to a wider contributor pool (cf. #1191). |

## The crux you must understand first

The current editor is **byte-identical** to the live game only because it shares one Python
codebase — it imports the truth directly:

- `pycats.combat.geometry.resolve_circle` — the single function that turns a facing-relative
  circle into an absolute on-screen circle. Render **and** hit-test both go through it.
- `pycats.combat.collapse.collapse` — the save-fold applied when serializing.
- `pycats.combat.data` types + the JSON serializer — the on-disk data shape.

A JS/TS app cannot `import` Python. **Fidelity path A means you reimplement those three things
in TypeScript and prove the reimplementation matches Python.** That proof — a cross-language
drift-guard — is the whole risk of path A. The good news below is that the surface needing a
guard is much smaller than it looks.

## Why A is safe here (verified in source, 2026-08-07)

The #1235 findings originally framed the whole geometry stack as a rounding minefield (a
`round(px * 5.4)` banker's-rounding trap, a facing-left mirror). A source re-check for #1307
narrowed that:

- **`Circle` geometry is integer.** `class Circle` in `pycats/combat/data.py` declares
  `dx: int`, `dy: int`, `r: int`. Authored box geometry is ints; the JSON stores ints.
- **`resolve_circle` is pure integer add/subtract — no rounding.** In
  `pycats/combat/geometry.py`:
  - facing right: `cx = origin_x + circle.dx`
  - facing left:  `cx = origin_x + width - circle.dx`  ← mirror is about the **body centre**
    (the #64 fix), not the left edge. A symmetric part (`dx == width/2`) is facing-invariant.
  - `cy = origin_y + circle.dy` (facing has no effect on y).
  Int in → int out. `circle_overlap` is `dx*dx + dy*dy <= r_sum*r_sum` — integer arithmetic,
  exact in both Python and JS at these magnitudes. **The data model and the hit-test are
  drift-free by construction.**
- **The banker's-rounding trap is NOT in the editor's geometry path.** `round(px * 5.4)` /
  `round(vel.x)` live in `pycats/core/physics.py` (movement) and `pycats/render/battle.py`
  (render scaling — `round(cx - left)`, `round(r)`). Those are game movement + on-screen
  scaling, not box authoring.
- **Float tuning fields round-trip identically.** `Hitbox` carries floats — `damage`,
  `base_knockback`, `knockback_growth`, `hitlag_mult`, and projectile `speed`/`vx`/`vy`/
  `gravity` (see `pycats/combat/data.py`). These are **stored, not computed**: a float written
  is the float read back, and JS numbers are IEEE-754 doubles exactly like Python floats. No
  drift surface — just match the serialization formatting.

### Drift-guard scope (the ruling)

**The cross-language drift-guard is required only for the render-preview scaling** (the
`× 5.4` + `round` that turns editor-space into on-screen pixels), and **only if** you want a
pixel-identical preview of how the game will draw the boxes. The core geometry authoring and
the hit-test need **no** cross-language guard — integer add/subtract can't drift.

If you do build the pixel-exact preview: the JS `Math.round` half-to-even gotcha bites, because
Python `round()` is banker's rounding (round-half-to-even), while JS `Math.round` is
round-half-up. Reproduce Python's rule for the scaled coordinates, and add a table-driven
drift-guard test comparing your TS scaler against the Python `round(px * PX_PER_UNIT)` output
across a range of inputs. `PX_PER_UNIT = 5.4` (see `pycats/core/physics.py` comment and
`pycats/config/`).

## What to build (fidelity path A, concretely)

1. **A TS port of the geometry contract:**
   - `resolveCircle(circle, originX, originY, facingRight, width)` — mirror the Python exactly,
     including the body-centre mirror for facing-left.
   - `circleOverlap` / `circlesOverlap` — integer squared-distance test.
   - the `collapse` save-fold (read `pycats/combat/collapse.py` — it had no rounding/float in
     the source scan; confirm before porting).
   - a JSON (de)serializer that reads and writes the **exact** current on-disk shape (see
     `docs/pycats-editor-data-schema-design.md`).
2. **A drift-guard test suite** (the path-A tax): golden vectors generated from Python, asserted
   against the TS port. Minimum: the render-preview scaler (§ drift-guard scope). Recommended:
   round-trip a corpus of existing character JSON through TS serialize→deserialize and diff.
3. **The React UI** — see rendering below.

## Rendering model (Q3)

```
┌─ SVG layer (on top) ───────┐
│  <circle> per hitbox/hurtbox │  ← drag, hover, select; DOM-native
│  = addressable DOM nodes     │     (Playwright getByRole targeting)
├─ Canvas 2D (underneath) ────┤
│  reference GIF / frame       │  ← raster underlay
└──────────────────────────┘
```

- **SVG** for the interactive boxes: each box is a DOM node, so drag/hover/select/keyboard and
  accessibility come mostly for free, and Playwright can target boxes by role/label.
- **Canvas 2D** underneath for the reference art (the GIF frame the boxes are drawn over).
- **No WebGL** — a handful of circles + one raster frame has no throughput need; the ruling
  declined it.

## Test/harness parity

The pygame editor's tests assert against Python truth. For the web editor, the intended harness
is **Playwright**, with box interactions targeted via `getByRole` (this is a reason SVG boxes
were preferred over an all-Canvas scene — Canvas boxes aren't DOM-addressable). Port the
behavioral assertions; add the drift-guard suite above as the cross-language backstop.

## Feature-parity inventory + phasing

Do not re-derive scope — the #1235 findings doc already enumerates it:

- **16-item feature-parity inventory** and the **phased plan** (P0 contract spike → … → P4):
  `docs/research/pycats-editor-react-rewrite-findings.md`.
- Plain-English pros/cons/advice companion: `docs/web-editor-1235-analysis-summary.md`.
- Current editor's data schema: `docs/pycats-editor-data-schema-design.md`.
- Current editor MVP + scope (for parity reference):
  `docs/pycats-editor-mvp.md`, `docs/pycats-editor-scope.md`.

**Start with P0 — the contract spike:** port `resolveCircle` + the serializer, stand up the
drift-guard, and render one character's boxes over its reference frame. Prove the contract
before building UI breadth.

## Hard prerequisite

The sibling repo **`pycats-react-editor` does not exist yet** and must be created by the repo
owner (a human) before implementation. Per the machine rules, an agent does not create or modify
repos outside the current working tree. The follow-on implementation epic (unfiled as of this
doc) names that repo creation as its blocker.

## Source-of-truth files to read (in the `pycats` repo)

| What | Where |
|------|-------|
| Circle types, Hitbox floats, JSON shape | `pycats/combat/data.py` |
| `resolve_circle`, overlap, `move_reach` | `pycats/combat/geometry.py` |
| Save-fold | `pycats/combat/collapse.py` |
| Render scaling + rounding (preview parity) | `pycats/render/battle.py`, `pycats/core/physics.py` |
| `PX_PER_UNIT` / scale config | `pycats/config/` |

## References

#1307 (this decision) · #1235 (research findings) · #792 (editor tracker) ·
#1191 (box-authoring epic) · #1197 (harness/replay) · #1206 / #1220 (datamine ghost-assist) ·
ADR-0008 (WYSIWYG editor). Decision index row: `docs/decisions-ledger.md` (2026-08-07, #1307).
