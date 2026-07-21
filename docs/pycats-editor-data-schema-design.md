# pycats-editor — data schema + editor screens/interactions (design)

**Status:** design (produced for #809, child of #792). Decisions ratified by the game-designer (interactive session, 2026-07-20). **No code** — this doc defines the contract a later SCOPE child cuts DEV slices from.

**Ratified basis:** [`docs/adr/0008-pycats-editor-wysiwyg-hitbox-hurtbox-editor.md`](./adr/0008-pycats-editor-wysiwyg-hitbox-hurtbox-editor.md) (decisions D0–D6) · [`docs/pycats-editor-mvp.md`](./pycats-editor-mvp.md) (what the tool is + MVP list).

**Research basis:** #782 [`docs/research/pm-hit-hurtbox-model-findings.md`](./research/pm-hit-hurtbox-model-findings.md) · #793 [`docs/research/hitbox-editor-scoping-findings.md`](./research/hitbox-editor-scoping-findings.md).

This doc covers the four things #809 asked for:

1. the JSON box-data schema (with a worked Nalio-jab example),
2. the `load_fighter_data` JSON extension + the edit→save→reload→replay seam,
3. the px ↔ `Circle(dx,dy,r)` coordinate mapping,
4. the editor screens/interactions (the MVP surface).

---

## 0. Design method + the one architectural decision

The schema was designed "twice" (three divergent candidates generated + compared, per the *design-an-interface* method):

- **A — thin mirror:** JSON ≈ the frozen dataclasses (already-collapsed windows); loader is a mechanical `dict→dataclass` hydrate; per-frame trace lives in an ignored `provenance` block.
- **B — frame-indexed canonical:** the per-frame table *is* the stored truth; `load_fighter_data` runs the collapse algorithm at load.
- **C — source + compiled:** one file with a rich per-frame `source` block + a collapsed `compiled` block the loader reads; a CI test recompiles source and asserts it matches compiled.

**Decision (game-designer, 2026-07-20): design around A + one idea borrowed from C.** B is rejected for pycats — the editor is a **separate** project (D1), so the per-frame→window collapse belongs *in the editor*, not in the pycats sim; and B makes golden-stability hang on a fragile load-time rewrite (goldens are sacred, #768). The chosen shape:

- the **runtime file is a thin static mirror** of the dataclasses (algorithm-free loader, byte-golden-safe, trivial migration);
- the editor writes an inline **`provenance`** block holding the per-frame authoring trace (so re-opening a move restores the author's work);
- a **drift-guard pytest** recompiles `provenance` and asserts it reproduces the canonical `hitboxes` (C's integrity idea, single-file, no bloat);
- an **optional `MoveData.hurtbox` override** field (default `None` → posture hurtbox) carries per-move hurtboxes.

C's full two-layer split stays documented as the **escalation path** (§7) if provenance ever needs to be a first-class reviewable artifact.

---

## 1. The JSON box-data schema

One file per fighter, `pycats/characters/data/<character>.json`, whose stem is the string `load_fighter_data` switches on (`nalio`, `birky`, `narz`, …).

**Two rules make the file thin and golden-safe:**

1. **Omission == the dataclass default.** Any field equal to its `data.py` default is dropped by the serializer. An absent field is byte-identical to today's Python that also omits it — so migrated data produces minimal JSON and existing goldens do not churn.
2. **Circles are inline `[dx, dy, r]` arrays** (three ints, fixed order) — the one intentional deviation from strict field-for-field mirroring, chosen because circles are the highest-count leaf. Everything else keeps its dataclass field name.

```jsonc
{
  "schema_version": 1,
  "character": "nalio",

  // ── FighterData fields, mirrored 1:1; omit any that equals its default ──
  "weight": 100,                 // omit -> 100
  // "gravity", "max_fall_speed", "move_speed", "dash_speed",
  // "jump_vel", "max_jumps"     // omit -> the config global
  // "stand_size": [w,h]         // omit -> None

  "hurtbox":        { "circles": [[20,15,14],[20,45,14]] },   // fighter posture (stand) body
  // "crouch_size": [w,h], "crouch_hurtbox": {"circles":[...]},   // omit -> None (cannot crouch)
  // "prone_size":  [w,h], "prone_hurtbox":  {"circles":[...]},

  "moves": {
    "jab": {
      "name": "jab", "in_air": false,
      "startup": 1, "active": 2, "recovery": 13,

      // Optional MoveData tail — omit for the default:
      //   "rehit_rate", "projectile_speed", "projectile_lifetime",
      //   "chargeable", "grants_recovery", "recovery_vy", "recovery_vx"

      // NEW optional per-move hurtbox override (see §1.2). Omit -> posture hurtbox.
      //   "hurtbox": { "circles": [[20,10,16],[20,40,16]] },

      // Already-COLLAPSED static hitboxes (the editor did the per-frame fold).
      // active_start/active_end omitted -> None -> the move's default window
      // [startup+1, startup+active]. Set both or neither (data.py __post_init__).
      "hitboxes": [
        { "circle": [54,27,19], "damage": 3.0, "angle": 83, "knockback_growth": 100.0, "set_knockback": 20 },
        { "circle": [44,28,13], "damage": 3.0, "angle": 83, "knockback_growth": 100.0, "set_knockback": 20 },
        { "circle": [34,29,15], "damage": 3.0, "angle": 85, "knockback_growth": 100.0, "set_knockback": 20 }
      ]
    }
  },

  // ── PROVENANCE — the loader NEVER reads this; the drift-guard test does ──
  // Per-move per-frame authoring trace + human notes. Structure is the editor's
  // convention; only the drift-guard test (§2.3) depends on the "frames" shape.
  "provenance": {
    "jab": {
      "note": "traced from PM3.6 Mario Attack11; active 2-3, all 3 boxes share the window",
      "source": "rukaidata ids 0/1/2, WDSK 20 / BKB 0 / KBG 100",
      "frames": [
        { "frame": 2, "boxes": [
            {"id":0,"circle":[54,27,19],"damage":3.0,"angle":83,"kbg":100.0,"wdsk":20},
            {"id":1,"circle":[44,28,13],"damage":3.0,"angle":83,"kbg":100.0,"wdsk":20},
            {"id":2,"circle":[34,29,15],"damage":3.0,"angle":85,"kbg":100.0,"wdsk":20} ]},
        { "frame": 3, "boxes": [
            {"id":0,"circle":[54,27,19],"damage":3.0,"angle":83,"kbg":100.0,"wdsk":20},
            {"id":1,"circle":[44,28,13],"damage":3.0,"angle":83,"kbg":100.0,"wdsk":20},
            {"id":2,"circle":[34,29,15],"damage":3.0,"angle":85,"kbg":100.0,"wdsk":20} ]}
      ]
    }
  }
}
```

### 1.1 Worked example — Nalio jab

The `hitboxes` block above is the **real** current Nalio jab (`pycats/characters/nalio_cat.py` `_JAB`, sourced from PM3.6 Mario Attack11): `startup=1, active=2, recovery=13` (total 16, default window `[2,3]`), three hitboxes all `damage=3.0`, `angle` 83/83/85, `set_knockback=20`, `knockback_growth=100.0`, `base_knockback=0.0`.

The collapse in action: provenance frames 2 and 3 are identical, so each box folds to a single run. Because that run equals the move's default window `[2,3]`, the `active_start`/`active_end` fields are **omitted** (they resolve to `None`) — reproducing the hand-written Python exactly. `base_knockback` (0.0) and the whole timing tail are dropped as defaults. Result: the serialized `hitboxes` are byte-equivalent to `_JAB.hitboxes`, so the jab golden does not move.

### 1.2 Per-move hurtbox override (new optional field)

Today a hurtbox is **fighter-posture-level** (`FighterData.hurtbox` / `crouch_hurtbox` / `prone_hurtbox`) — there is no per-move slot, so per-move/per-frame hurtbox authoring has nowhere to land. Proposal (a `data.py` change a later DEV slice makes, flagged here for review, **not** done in #809):

> add `hurtbox: Hurtbox | None = None` to `MoveData`, defaulting `None`.

Consumers that resolve a fighter's active hurtbox check `move.hurtbox or fighter.hurtbox`. Absent key → `None` → posture hurtbox, **byte-identical to today** (golden-safe; the field is inert until a consumer reads it). The JSON carries at most **one already-collapsed static** `Hurtbox` per move under the `hurtbox` key. Per-frame hurtbox authoring in the editor collapses to this single override by **union** of the frames' circles (the safe direction — never under-covers the body); a varying hurtbox that the always-active runtime cannot express is recorded in provenance with a `hurtbox_varies_collapsed_to_union` note.

### 1.3 The collapse (editor-side, defined here as the contract)

The editor owns the per-frame→window fold; the runtime never runs it. Defined so the editor and the drift-guard test agree:

1. **Index by identity.** Regroup the frame-major `provenance.frames` into box-major streams keyed by the author-assigned `id`. Two frames' boxes are "the same box" **iff they share `id`** — geometry equality is deliberately *not* identity (two boxes may momentarily coincide yet stay distinct hits).
2. **Run-length fold.** Walk each id's frames in order, extending a run while *all* hold: (a) contiguity (`frame == prev+1`; a gap closes the run), (b) circle unchanged, (c) scalars (`damage/angle/bkb/kbg/wdsk`) unchanged. On break, emit one `Hitbox(circle, …scalars…, active_start=run.first, active_end=run.last)` and open a new run.
   - static box → one run → one windowed `Hitbox`;
   - **moving box → geometry changes each frame → a staircase of 1-frame windows** (the ratified static-staircase; zero engine change);
   - blinking box (gap) → two windows under one id.
3. **Default-window canonicalization (golden-safe).** If *every* emitted `Hitbox` has window exactly `[startup+1, startup+active]`, rewrite them to `active_start=active_end=None`. This is what keeps single-window moves byte-identical to today's `None`-window Python.
4. **Deterministic order.** Sort the emitted tuple by `(window_start, priority, id)` so tuple order — and therefore overlap resolution and golden bytes — is stable regardless of author edit order.

---

## 2. The serialization seam

### 2.1 `load_fighter_data` extension (thin, algorithm-free)

A JSON branch in front of today's import switch (`pycats/combat/data.py`):

```
load_fighter_data(character):
    path = CHARACTER_DATA_DIR / f"{character}.json"
    if path.exists():
        return _fighter_from_json(json.load(path))   # new branch
    ...existing Python import switch, unchanged (default cat, etc.)...
```

`_fighter_from_json` is a mechanical hydrate — **no reshaping, no window synthesis, no unit scaling** (values are already px/frames as authored):

- `Circle(*triple)` for every `[dx,dy,r]`; `Hurtbox(circles=tuple(...))`.
- `Hitbox(**subset)` — pass only keys present; the frozen dataclass supplies defaults. This keeps a **single default table** (the dataclass) so the loader cannot drift from it.
- `MoveData(**subset)` incl. the optional `hurtbox` override; `FighterData(**subset)`.
- JSON arrays deserialize to lists → re-`tuple()` every collection (`hitboxes`, `circles`, `*_size`) since the dataclasses are frozen and goldens depend on tuple identity.
- Validation is delegated to the existing `__post_init__` checks (paired window, window-in-duration, same-start-same-window). The loader adds only a `schema_version` assert.
- `doc["provenance"]` is never touched by the loader.

### 2.2 Edit → save → reload → replay (the round-trip; determinism boundary)

The editor is an **offline data-emitting tool**, never a live in-match mutator — box `dx/dy/r` feed the deterministic sim and are serialized into golden snapshots via `snapshot()` (#768), and pycats' dataclasses are frozen. The loop:

```
   editor (pycats-editor, separate project)
   ─ author per-frame boxes on a fighter ─▶ collapse (§1.3) ─▶ write <character>.json
                                                                     │
   pycats ─ load_fighter_data(character) ◀── reload (fresh process / fresh load) ──┘
          ─ replay in the deterministic sim ─▶ goldens/behavior reflect the new boxes
```

No live mutation of a running match; a box change lands only through a serialize→reload cycle. This is the boundary that keeps the sim deterministic and the golden contract intact.

### 2.3 Drift-guard verify test (the one idea borrowed from C)

A pytest in pycats: for each `<character>.json`, **recompile** `provenance` (run §1.3 over the per-frame trace) and assert the result equals the committed canonical `hitboxes` (and per-move `hurtbox` override). A mismatch means someone hand-edited the canonical boxes without updating the trace (or vice-versa) — the test fails and names the move. Cheap (small per-frame tables), single file, no CI-gate dependency beyond the normal suite. Moves with no `provenance` entry are skipped (migrated data that predates the editor — see §2.4).

### 2.4 Migration of today's Python

Cheapest of the three candidates: because the schema mirrors the dataclasses and "omit == default," migration is a mechanical `dataclass → dict` dump that drops default-valued fields (built from `dataclasses.fields()` + default comparison). Today's `nalio`/`birky`/`narz`/`default`/`GETUP_ATTACK` convert with no hand-tuning, and a golden test (`load_fighter_data("nalio")` from Python == from JSON) is trivial. Migrated moves start with **no `provenance`** (there is no per-frame trace in the Python); the first time the editor opens a move it reverse-collapses the windows into per-frame rows (replicate each box across its window) to seed the trace.

---

## 3. Coordinate mapping (px ↔ `Circle(dx,dy,r)`)

Ground truth from `pycats/combat/geometry.py` and `pycats/config.py`:

- `Circle(dx, dy, r)` are **pixels**, offset from the fighter's **top-left origin**, **facing-RIGHT-relative**.
- `resolve_circle(circle, origin_x, origin_y, facing_right, width)` → absolute center:
  - facing right: `cx = origin_x + dx`
  - facing left:  `cx = origin_x + width - dx` (mirror **around body centre**, so a symmetric part `dx == width/2` is facing-invariant; #64)
  - `cy = origin_y + dy` (facing-invariant)
- `PX_PER_UNIT = 5.4` (config) is the Smash-units→px scale used to *author* sizes: `r = round(size_units × PX_PER_UNIT)` (#120). The fighter data stores the **px result**, not units.

**Implication for the editor:** it works in **px directly** — a circle dragged on the canvas maps to `dx/dy/r` with no scaling, and round-trips to the same values pycats replays. Two conveniences worth offering (SCOPE decides): (a) a read-out that also shows `r / PX_PER_UNIT` in units for parity notes; (b) drawing uses the **same** path as the game — `resolve_circle` for hurt/hit circles, exactly as `render_hitbox_overlay` already does (`pycats/render_battle.py`) — so the editor canvas and the live overlay are pixel-identical. The editor has no live `Attack` objects, so it resolves `Circle`s directly (the hurtbox path), rather than reading `atk.resolved`.

---

## 4. Editor screens / interactions (MVP surface)

Mapping the MVP list ([`docs/pycats-editor-mvp.md`](./pycats-editor-mvp.md)) to concrete UI. One primary screen — a **move workbench** — plus chrome (**pygame_gui**, editor-only dep, D4) and GIF decode (**Pillow**, editor-only dep, D5).

**Layout (single window):**

- **Canvas (center):** the fighter drawn at a chosen origin; hit circles + hurt circles drawn via `resolve_circle` (game-identical). Behind/beside it, the #777 Mario reference GIF for the matching move.
- **Timeline (bottom):** one cell per move-clock frame `1..total`, banded by phase (startup / active / recovery). The playhead marks the current frame.
- **Inspector (side):** the selected box's `dx/dy/r` + scalars (damage/angle/kbg/bkb/wdsk), editable; the move's `startup/active/recovery`; the provenance `note`.

**Interactions (each MVP item → behavior):**

| MVP item | Interaction |
|---|---|
| edit hit + hurt **per frame** | select a box on the canvas; drag to move, handle to resize; edits apply to the **current frame** (creating/extending that box's per-frame entry). Add/remove boxes per frame. |
| **scrub** back/forth | drag the playhead or ←/→ keys; canvas + inspector update to that frame. |
| **loop** playback | play/pause; loops `1..total` at the sim frame-rate; a duration read-out shows total frames vs the Mario GIF's frame count (the compare check). |
| **toggle** box display | show/hide hitboxes, hurtboxes, and the GIF independently. |
| **overlay** fighter on the GIF goldens | draw the pycats fighter over the #777 GIF at a shared origin (trace mode). |
| **scale / translate** the GIF | move + scale the GIF to sit **beside** (side-by-side compare) or **directly behind** (trace) the fighter; scale/offset are view-only, not saved into fighter data. |

**Save:** runs the collapse (§1.3), writes `<character>.json` (canonical `hitboxes` + `hurtbox` override + `provenance` trace). **Open:** reads the file, prefers `provenance.frames` to restore the per-frame working state; falls back to reverse-collapsing the canonical windows (§2.4) for migrated moves.

Reused from pycats (D1): `resolve_circle`, the `render_hitbox_overlay` drawing approach, `MoveData` timing, and `load_fighter_data` for round-trip verification.

---

## 5. What's decided vs open (for the SCOPE child)

**Decided (this doc):** the runtime file shape (thin static mirror + inline provenance); the loader hydrate; the drift-guard test; the collapse contract; the coordinate mapping; the per-move `MoveData.hurtbox` override proposal; the editor screen model.

**Open — for SCOPE / DEV to resolve when slicing:**

- Exact directory (`pycats/characters/data/` vs a top-level `data/`) and whether the `pycats-editor` repo vendors pycats as a dependency or a submodule (D6 repo is created at first build slice).
- Whether migration flips **all** fighters to JSON at once or one at a time (goldens must stay green either way).
- pygame_gui vs a hand-rolled minimal toolkit if pygame_gui proves heavy for the MVP.
- Projectile moves (Nalio fireball) — box authoring is in scope, but the projectile *path* is physics, not per-frame authoring; likely a later slice.

---

## 6. Out of scope (unchanged from the ratified decisions)

- Building the editor or the loader change (SCOPE → DEV children, downstream).
- Creating the `pycats-editor` repo (D6: at first build slice).
- Non-Nalio fighters as authoring targets; game-time consumption of *per-frame* box motion (deferred, D2 — the runtime stays static).

---

## 7. Escalation path — candidate C, if provenance must become first-class

If the inline-provenance + drift-guard approach proves insufficient (e.g. provenance needs to be reviewed as a primary artifact, or the drift-guard's per-move skip for migrated data becomes a liability), escalate to candidate **C**: split each fighter file into a per-frame `source` block and a collapsed `compiled` block bound by a `link` hash, with a **mandatory** CI recompile-and-compare gate. Same collapse contract (§1.3); the difference is the source becomes a committed, verified layer rather than an advisory one. Cost: doubled diffs, file bloat, a hard dependency on the verify gate. Not needed for the MVP.

---

## References

#809 (this design) · #792 (tracker) · ADR-0008 + `docs/pycats-editor-mvp.md` (ratified D0–D6) · #793 / #782 (research) · #777 (Mario GIF goldens) · #778 (compare view, folded in) · #310 (position = feel, not lookup) · #768 (box moves are sim-affecting) · #309 (`zone_dy` body-relative anchoring) · #120 (`PX_PER_UNIT` units→px) · #64 (facing-mirror around body centre) · #204/#211/#212 (per-hitbox windows + set-knockback, already in `data.py`).
