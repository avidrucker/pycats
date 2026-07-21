# pycats-editor — SCOPE: DEV-slice decomposition

**Status:** scope (produced for #826, child of #792 — stage 4 of 5: research → decision → design → **scope** → build). Architect-mode output (yegor-architect): a written decomposition, **no code**. Each slice below is a ≤~60m courier task with a declared blocking edge and an able-to-fail regression test; DEV children are filed **one-at-a-time downstream** after a human greenlight (per the #792 lazy-decomposition rule).

**Design basis (do not re-litigate):** #809 [`docs/pycats-editor-data-schema-design.md`](./pycats-editor-data-schema-design.md) · ADR-0008 · [`docs/pycats-editor-mvp.md`](./pycats-editor-mvp.md).

The work splits across **two repos** (D1): the **pycats** runtime side (schema + loader + drift-guard, all golden-safe) and the **separate `pycats-editor`** repo (the WYSIWYG tool). The two chains are independent except where noted; the editor's save/open reuses the collapse the runtime side already needs for its drift-guard test.

---

## Product Breakdown Structure

Eight units, current completion:

| # | Unit | % | Home |
|---|---|---|---|
| PBS-1 | `MoveData.hurtbox` per-move override (data model) | 0% | pycats |
| PBS-2 | JSON schema + `_fighter_from_json` hydrate + `load_fighter_data` branch | 0% | pycats |
| PBS-3 | Python→JSON migration dump | 0% | pycats |
| PBS-4 | Collapse algorithm (§1.3) as an importable module | 0% | shared (pycats test + editor) |
| PBS-5 | Drift-guard pytest | 0% | pycats |
| PBS-6 | `pycats-editor` repo bootstrap + fighter load (D6) | 0% | pycats-editor |
| PBS-7 | Move-workbench UI (canvas / timeline / inspector / per-frame edit) | 0% | pycats-editor |
| PBS-8 | GIF compare (overlay / side-by-side / scale-translate) | 0% | pycats-editor |

---

## The slices

Naming: **R#** = pycats runtime side, **E#** = editor side. "Blocks" = the slice(s) that must land first. Every slice touching `data.py` / `load_fighter_data` must ship **byte-identical goldens** until a consumer reads the new data (the field/branch is inert on arrival).

### Runtime side (pycats repo — golden-safe)

**R1 — add `MoveData.hurtbox: Hurtbox | None = None`** (design §1.2).
Add the optional field to the frozen dataclass; default `None`. Nothing reads it yet → inert.
*Test (able-to-fail):* `MoveData(...)` accepts a `hurtbox=` kwarg; omitted → `None`; a golden snapshot of an existing fighter is unchanged. Reverting the field makes the kwarg test error.
*Blocks:* none. *Est:* S (~20m).

**R2 — resolve `move.hurtbox or fighter.hurtbox` at the active-hurtbox site** (design §1.2).
Change the one place that resolves a fighter's active hurtbox for hit-detection/overlay to prefer a move override when present. Absent override → posture hurtbox, byte-identical to today.
*Test:* a synthetic move with a `hurtbox` override resolves to the override's circles; without → posture. Existing goldens unchanged (no shipped move sets it yet).
*Blocks:* R1. *Est:* M (~40m). *Note:* audit every reader of `_active_hurtbox` / `FighterData.hurtbox` so none is missed.

**R3 — `_fighter_from_json(doc) -> FighterData` pure hydrate** (design §2.1).
Mechanical dict→dataclass: `Circle(*triple)`, `Hurtbox`, `Hitbox(**subset)`, `MoveData(**subset)`, `FighterData(**subset)`; re-`tuple()` every collection; `schema_version` assert; validation delegated to `__post_init__`; `provenance` untouched. No wiring into `load_fighter_data` yet.
*Test:* a hand-written dict fixture (the worked Nalio-jab from §1) hydrates to a `FighterData` equal to the Python `load_fighter_data("nalio")`; tuple identity holds; a paired-window violation raises via `__post_init__`.
*Blocks:* R1 (so the hydrate can round-trip the `hurtbox` key). *Est:* M (~50m).

**R4 — wire the JSON branch into `load_fighter_data`** (design §2.1).
Front the import switch with `if (CHARACTER_DATA_DIR / f"{character}.json").exists(): return _fighter_from_json(...)`. No JSON shipped yet → branch inert; Python switch unchanged.
*Test:* with a fixture JSON on a temp `CHARACTER_DATA_DIR`, `load_fighter_data` returns the hydrated fighter; with no file, the Python path is taken (existing tests still green).
*Blocks:* R3. *Est:* S (~30m).

**R5 — migration dump: Python `FighterData` → minimal JSON** (design §2.4).
A `dataclasses.fields()` + default-comparison serializer that drops default-valued fields and emits inline `[dx,dy,r]` circles. Produces `<character>.json`.
*Test:* round-trip — `load_fighter_data("nalio")` from Python **==** from the generated JSON (and same for birky/narz/default/GETUP_ATTACK). This is the slice that *may* flip a fighter to JSON; goldens stay green because the round-trip is equality-checked.
*Blocks:* R4. *Est:* M (~50m). *Decision at slice time:* flip all fighters at once vs one-at-a-time (§5).

**R6 — collapse algorithm module** (design §1.3).
Pure `collapse(provenance_frames) -> tuple[Hitbox, ...]`: index-by-id → run-length fold → default-window canonicalization → deterministic sort. Lives in an importable module both the drift-guard test and the editor use (see Risk-2 on where it physically lives).
*Test:* the worked Nalio-jab provenance (frames 2 & 3 identical, all 3 boxes) collapses to exactly `_JAB.hitboxes` with `active_start/end` canonicalized to `None`; a moving box yields a 1-frame-window staircase; a blinking box yields two windows under one id.
*Blocks:* R1 (Hitbox/MoveData shapes). Independent of R3–R5. *Est:* M (~60m).

**R7 — drift-guard pytest** (design §2.3).
For each shipped `<character>.json` with a `provenance` block, assert `collapse(provenance)` equals the committed canonical `hitboxes` (+ per-move `hurtbox` override). Moves with no provenance are skipped.
*Test (able-to-fail):* hand-edit a canonical hitbox in a fixture JSON without touching its provenance → the guard fails and names the move; matching data → passes.
*Blocks:* R6 + at least one provenance-bearing JSON (a fixture is enough; does not require R5's real migration). *Est:* S (~30m).

### Editor side (separate `pycats-editor` repo)

**E0 — repo bootstrap + load a fighter (D6, head of the editor chain).**
Create the `pycats-editor` repo; resolve pycats-as-dependency vs git submodule (§5); minimal pygame-ce window that imports pycats and calls `load_fighter_data("nalio")`, printing the moves. This is the first slice that creates the repo.
*Test:* a smoke test asserting the app boots headless and loads Nalio's `MoveData`.
*Blocks:* soft-after R4 (round-trip verify is nicer once JSON loads, but not required to boot). *Est:* M (~50m). *Gated:* pycats-editor is a new repo; dep choices need human sign-off. **pygame_gui + Pillow are new deps → human approval before adding (CLAUDE.md dependency gate).**

**E1 — canvas: draw fighter + hit/hurt circles via `resolve_circle`** (design §3, §4).
Reuse the game's `resolve_circle` + the `render_hitbox_overlay` drawing approach so the canvas is pixel-identical to the live overlay. Static single-frame render first.
*Test:* rendering Nalio's jab at a fixed origin produces circles at the same centres `resolve_circle` yields for the game.
*Blocks:* E0. *Est:* M (~60m).

**E2 — timeline + scrub** (design §4).
Frames `1..total` banded startup/active/recovery; playhead; ←/→ + drag to scrub; canvas follows the frame.
*Test:* selecting frame N updates the displayed box set to that frame's boxes.
*Blocks:* E1. *Est:* M (~50m).

**E3 — inspector: edit selected box + move timing** (design §4).
Editable `dx/dy/r` + scalars (`damage/angle/kbg/bkb/wdsk`) for the selected box; editable `startup/active/recovery`; provenance `note`.
*Test:* editing a field updates the in-memory box; canvas reflects it.
*Blocks:* E1 (needs a selectable box). Parallel to E2. *Est:* M (~50m).

**E4 — per-frame box authoring on the canvas** (design §4, §1.3 contract).
Drag to move / handle to resize writes the **current frame's** provenance entry; add/remove boxes per frame; identity via author-assigned `id`.
*Test:* dragging a box on frame N leaves frame N±1 unchanged; the per-frame provenance model records the edit under the box's `id`.
*Blocks:* E2 + E3. *Est:* M (~60m).

**E5 — save: collapse + write `<character>.json`** (design §1.3, §4).
On save, run **R6's collapse** over the per-frame provenance, write canonical `hitboxes` + `hurtbox` override + the `provenance` trace to `<character>.json`.
*Test:* authoring the Nalio jab per-frame and saving produces JSON whose `hitboxes` round-trip-load (via pycats `load_fighter_data`) equal to `_JAB.hitboxes`; the file passes R7's drift-guard.
*Blocks:* E4 + R6 (+ R4 for the round-trip assertion). *Est:* M (~60m).

**E6 — open: restore per-frame state** (design §2.4, §4).
Read a file; prefer `provenance.frames` to restore the working state; fall back to reverse-collapsing canonical windows (replicate each box across its window) for migrated moves with no provenance.
*Test:* open→edit-nothing→save is a no-op (byte-stable) for a provenance-bearing file; a provenance-less migrated move reverse-collapses to per-frame rows.
*Blocks:* E5. *Est:* M (~50m).

**E7 — GIF compare: overlay / side-by-side / scale-translate** (design §4, MVP; folds in #778/#777).
Pillow-decode the matching #777 Mario GIF; toggle hit/hurt/GIF independently; draw the fighter over the GIF (trace) or beside it (compare); scale + translate the GIF (view-only, never saved); a duration read-out shows fighter total-frames vs GIF frame-count (the compare check).
*Test:* a decoded GIF's frame count is read and displayed; scale/offset never mutate saved fighter data.
*Blocks:* E1 (independent of the E2–E6 edit chain). *Est:* M (~60m). *Gated:* Pillow dep (see E0).

**E8 — chrome (pygame_gui or hand-rolled)** (design §4, D4).
Play/pause loop, toggle controls, file dialogs, the duration read-out — via pygame_gui, or a minimal hand-rolled toolkit if pygame_gui proves heavy (§5).
*Test:* play loops `1..total` at the sim frame-rate; pause holds the frame.
*Blocks:* soft-after E1. *Est:* M (~50m). *Decision at slice time:* pygame_gui vs hand-rolled.

---

## Dependency graph (blocking edges)

```
pycats side:   R1 ─┬─ R2
                   ├─ R3 ── R4 ── R5
                   └─ R6 ── R7
editor side:   E0 ── E1 ─┬─ E2 ─┐
                         ├─ E3 ─┴─ E4 ── E5 ── E6
                         ├─ E7
                         └─ E8
cross-repo:    R6 ─▶ E5 (editor save reuses the collapse)
               R4 ─▶ E0/E5 (round-trip verify; soft for E0, needed for E5's assertion)
```

**Head of the editor chain:** **E0** (creates the `pycats-editor` repo, D6). Nothing in the editor chain starts before it.
**Recommended first courier task overall:** **R1** — smallest, unblocks both R2/R3 and R6, zero golden risk.

---

## Issues (current, already affecting the build)

1. **Collapse lives in two places by design.** R6's algorithm is needed by both the pycats drift-guard test **and** the editor's save. Physically it can't live in the editor if the pycats test must import it. Resolution proposed in Risk-2.
2. **New editor dependencies are gated.** pygame_gui (D4) + Pillow (D5) are not yet approved; E0/E7/E8 cannot add them without human sign-off (CLAUDE.md). File the dependency-approval ask before E0.
3. **`MoveData.hurtbox` is a real `data.py` change** touching the frozen model + every hurtbox reader (R1/R2). It must land golden-safe and be audited for all consumers before the editor authors per-move hurtboxes.

## Risks (future, with probability × impact)

1. **Golden churn on migration (R5)** — *prob: med, impact: high.* Flipping a fighter to JSON could move a golden if the round-trip isn't exactly equal. *Mitigation:* R5's test is a strict Python==JSON equality gate; flip one fighter at a time; keep the Python literal until the JSON round-trips clean.
2. **Where does the collapse module live? (R6)** — *prob: high, impact: med.* If it lives only in the editor repo, the pycats drift-guard can't import it; if it lives in pycats, the editor imports pycats anyway (D1) so that's fine — **recommend the collapse ships in pycats** (`pycats/combat/collapse.py` or a test util) and the editor imports it. Settle at R6.
3. **pygame_gui too heavy for the MVP (E8)** — *prob: med, impact: low.* *Mitigation:* E8 is explicitly either/or; fall back to a hand-rolled minimal toolkit; nothing downstream depends on the chrome library choice.
4. **Per-frame hurtbox can't be expressed by the always-active runtime** — *prob: low, impact: med.* A varying hurtbox collapses to the union of frames (§1.2, safe over-cover); recorded in provenance with a `hurtbox_varies_collapsed_to_union` note. No engine change; accept the over-cover for the MVP.
5. **Projectile moves (Nalio fireball)** — *prob: med, impact: low.* Box authoring is in scope; the projectile *path* is physics, not per-frame box authoring. *Mitigation:* out of the core chain; file as a later standalone slice after E6.

---

## Open questions to settle at slice time (from #809 §5)

- **Data directory:** `pycats/characters/data/<character>.json` vs a top-level `data/` — settle at R4.
- **pycats-editor ← pycats:** dependency (pip/editable install) vs git submodule — settle at E0.
- **Migration cadence:** all fighters to JSON at once vs one-at-a-time — settle at R5 (goldens green either way).
- **Chrome toolkit:** pygame_gui vs hand-rolled — settle at E8.
- **Projectile authoring:** separate later slice after E6.

## Out of scope

Writing any slice (downstream DEV children, one-at-a-time after greenlight). Re-opening #809's ratified schema/loader/collapse decisions. Game-time consumption of per-frame box **motion** (D2 — runtime stays static). Non-Nalio fighters as authoring targets for the MVP.

## References

#826 (this scope) · #809 (design) · #792 (tracker) · ADR-0008 + `docs/pycats-editor-mvp.md` · #793/#782 (research) · #768 (box moves are sim-affecting) · #778/#777 (compare substrate + GIF goldens) · #310 (position = feel) · #120 (`PX_PER_UNIT`) · #64 (facing-mirror).
