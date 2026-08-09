# PM/Brawl-faithful auto-pan / auto-zoom camera — scope & decomposition (#803)

> **Agent:** ELDERBERRY · **Authored:** 2026-08-08 · **Ticket:** #803

Scoping spike (≤60m, scope-not-build) for an auto-panning / auto-zooming in-battle camera as
faithful to Project M / Brawl as the engine allows. Output: the code sites, prerequisites, and
open decisions a decomposition needs — plus a **proposed ordering of ≤60m DEV microtasks**. No
implementation.

This spike runs **after** #1315 (throwaway follow+zoom prototype, GO) and synthesizes the
now-available primary inputs rather than re-researching from scratch — see the #803 body's
"Scope refresh — 2026-08-08" note.

## Recommendation

The production camera is a **presentation-only viewport layer with an identity default**, built
by porting the #1315 prototype's proven pieces onto main behind an off-by-default flag, then
replacing its two throwaway scaffolds with sourced data. The work decomposes into **8 ≤60m DEV
microtasks** (§5), of which the first four are buildable the moment **#1304 Q1** ratifies
"build moving"; the rest are gated on **#789** (KO-in-world), **#790** (per-stage stage data),
and **#1331** (feel-number values, filed by this spike). Only **#1304** gates the *start*; the
other three gate later tasks (§6).

## Q1 — What the PM/Brawl camera does (synthesized from primary sources)

Grounded in the two code/data-verified studies already on main — not re-derived here:

- **`docs/research/2026-08-07-camera-melee-brawl-pm-comparison.md` (#1279)** — code-verified from
  the Melee decomp (`doldecomp/melee`). The camera: enumerates subjects → builds their min/max
  bounding box (`CameraBounds`, `camera.c`) → scales the box by a per-count weight → fits distance
  then clamps it between a zoom floor (`Stage_GetCamZoomRate`) and a depth ceiling
  (`Stage_GetCamMaxDepth`) → eases per-frame with a lerp clamped to `[0.0001, 1.0]`. Subject
  positions are clamped against `Stage_GetCamBounds…Offset()` before boxing.
- **`docs/research/2026-07-31-pm-fd-blast-zone-floats.md` (#790)** — datamined PM 3.6 Final
  Destination floats at `PX_PER_UNIT ≈ 5.4`. Two per-stage boxes:

  | Box | Role | Beyond each screen edge (L/R · top · bottom) |
  |-----|------|----------------------------------------------|
  | **CamLimit** (inner) | camera pan-limit — on-screen boundary | +438 · +346 · +162 px |
  | **Dead** (outer) | KO / blast boundary | +848 · +745 · +486 px |

  Verbatim from #790: *"Camera pan-limit ≠ blast zone… CamLimit = (±170, +114/−80) — a separate,
  tighter boundary."* Clamping camera pan + zoom-out to **CamLimit** keeps the stage framed with
  no explicit visibility check — it falls out of the clamp.

**Behavior pycats will port** (from #1315, felt-approved): bounding box over all alive fighters →
flat margin → zoom-to-fit with zoom-in/out clamps → pan-to-center → per-frame lerp smoothing →
camera on/off toggle. **Deliberately OUT** (per the #1308 spec): the Melee per-count weight table
`{1.5, 1.32, 1.16, 1.0}` and the off-screen magnifying-glass bubbles.

## Q2 — pycats render→screen pipeline, and where the viewport sits

The sim renders onto a fixed **960×540** surface; the window scale is a separate, later step:

- **World draw** — `BattlePresenter.show` (`pycats/sim/presenters.py`) calls
  `render_battle(self.screen, players, platforms)` then `render_attacks(self.screen, attacks)`
  onto the 960×540 game surface.
- **Window scale** — `DisplayManager.present` (`pycats/shell/display_manager.py`) blits that
  surface through `display.scale_surface(...)` up to the window (letterbox in fullscreen, exact
  fill windowed), then `pygame.display.flip()`. The `zoom_toast` and HUD are drawn here in
  **window space**, above the scene, so they never land in the 960×540 sim/goldens.

**The viewport transform sits at the world-draw call**, between sim state and the 960×540 surface
— exactly where the #1315 prototype's `Camera.render_world` sat: render the extended world onto an
oversized surface at a constant BASE offset, crop the camera sub-rect, scale to 960×540. The
window-scale step downstream is unchanged.

**Scoping finding — two present paths, not one.** The #1315 prototype wired the camera into the
**live** path only (`pycats/screens/battle_screen.py` via `pycats/shell/app.py`). The **sim/replay**
path (`BattlePresenter` in `pycats/sim/presenters.py`, used by `watch.py`) draws the world
independently. A production camera must route **both** through one offset-aware seam, or it will
apply to the live game but not to recordings/replays. This is the foundational DEV task (§5, D1).

Blast zones today are **screen-coupled**: `Fighter._outside_blast_zone`
(`pycats/entities/fighter.py`) tests `rect.right < -BLAST_PADDING_X` etc. against `SCREEN_WIDTH`/
`SCREEN_HEIGHT` with `BLAST_PADDING = 50`, `BLAST_PADDING_TOP = 150`, `BLAST_PADDING_X = 100`
(`pycats/config/stage.py`). Under a moving camera, "beyond the screen edge" no longer means "dead"
— which is the decouple in Q3.

## Q3 — Prerequisites: the KO-in-world decouple

A moving camera breaks the screen-coupled KO test. Today KO = "fighter rect past a fixed screen-edge
padding." Once the camera pans/zooms, the screen edge is no longer a fixed world boundary, so KO must
be tested against a **world-fixed** blast box, independent of what the camera currently frames.

- **What must decouple:** `Fighter._outside_blast_zone` must compare fighter world position against
  a **world-coordinate** Dead box (the sourced ±848/745/486 geometry, or its per-stage successor),
  not against `SCREEN_WIDTH ± BLAST_PADDING_*`. The camera then becomes free to frame any sub-region
  without moving the KO boundary.
- **Interaction with #789:** #789 (`decision`, `deferred`) owns the near-term FD blast-zone **value
  model** under the *current fixed* camera. The camera work does **not** ratify #789's values — but
  it **consumes the decouple** #789 shares: both need blast zones expressed in world coordinates
  rather than screen padding. The #1315 prototype faked this with the `EXPERIMENTAL_WIDE_BLAST` flag
  (hardcoded ±848/745/486 px); production replaces that fake with the #789 world-coordinate model.
  **Order: #789's decouple lands first, then the camera frames against it** (§5, D5).
- **World-unit rendering (#80, CLOSED):** the research on decoupling the sim from pixel coordinates
  is done; the camera does **not** require a full world-unit rewrite — the #1315 prototype works in
  the existing pixel space with a pixel BASE offset. World-unit rendering remains a larger,
  independent track, not a camera prerequisite.

## Q4 — Design shape: presentation-only, identity-default viewport

#45's Q4 sketch (`docs/research/screen-camera-sizing-findings.md`) is **validated** by #1315: a
presentation-only viewport layer — bounding-box → zoom-to-fit → clamp to CamLimit → lerp — that
**defaults to an identity transform**, so with the camera off the 960×540 surface is byte-identical
and the sim goldens stay green (#1315: 2277 passed, 1 xfailed, camera off). The camera is a *pure
function of sim state onto the surface*; it never feeds back into the sim, so it cannot perturb
physics, KO, or determinism. Off-screen magnifying-glass bubbles from #45's sketch stay **out** of
the first production cut (matching #1315 / #1308).

## Gap table — what's answered vs. still open

| Question | Status | Source |
|----------|--------|--------|
| Q1 — PM/Brawl camera behavior | **Answered** — synthesized, not re-derived | #1279, #790, #1315 |
| Q2 — where the viewport sits | **Answered** — world-draw call; two present paths | `presenters.py`, `display_manager.py`, #1315 |
| Q3 — decouple prerequisites | **Scoped** — KO-in-world via #789; #80 not required | #789, `fighter.py`, `config/stage.py` |
| Q4 — presentation-only, identity default | **Validated** — byte-identical camera-off | #45, #1315 |
| Feel numbers (zoom caps, ease) | **Open decision** — see §6 | #1315 (felt), not ratified |
| Per-stage CamLimit/Dead as stage data | **Open** — currently module constants | #790, #661 |

## §5 — Proposed decomposition into ≤60m DEV microtasks

Ordered; each is a bounded ≤60m unit. **D1–D4 are buildable once #1304 Q1 = "build moving"** (§6);
D5 is gated on #789; D6 on #790/#661; D7 on a feel-numbers decision.

| # | DEV microtask | Gate | Code sites (by landmark) |
|---|---------------|------|--------------------------|
| **D1** | Route both present paths through one offset-aware world-draw seam (live `battle_screen` + sim/replay `BattlePresenter`), so a single camera hook covers game and recordings. | #1304 | `render_battle`/`render_attacks` (`render_battle` module); `BattlePresenter.show` (`sim/presenters.py`); `battle_screen` render |
| **D2** | Port the offset-threading from the throwaway branch to main — `offset=(0,0)` params on `render_battle`/`render_attacks`/`render_tail`/`draw_dizzy_stars`/`draw_timer_bars`/`draw_grabs_left_dots`. Camera OFF; identity default; goldens stay green (revert-check: default path byte-identical). | #1304 | `render/battle.py`, `render/body.py`, `render/status.py` |
| **D3** | Port the `Camera` framer (bounding-box over alive fighters → fit → clamp to CamLimit → pan/zoom lerp) behind an off-by-default flag + toggle. No golden change (camera off). | #1304 | new `render/camera.py`; `battle_screen`; `shell/app.py` toggle |
| **D4** | Add camera-ON golden baselines (new fixtures at representative scales/centers); camera-off goldens unchanged. | #1304 | `tests/golden/…`, `tests/test_render_*` |
| **D5** | Replace `EXPERIMENTAL_WIDE_BLAST` fake KO distances with the KO-in-world-coordinates model; frame against sourced world-bound Dead geometry, not a hardcoded box. | **#789** | `Fighter._outside_blast_zone` (`entities/fighter.py`), `config/stage.py` |
| **D6** | Formalize CamLimit / Dead as per-stage **stage data** (the PM `.pac` bones), not module constants living in `camera.py`. | **#790/#661** | `config/stage.py` / stage descriptor; `render/camera.py` |
| **D7** | Finalize feel numbers (zoom-in/out caps, ease rates) as a designer decision or sourced values; record `FOUND`/`TUNED` per RULES → "Changing values". | **#1331** | `render/camera.py` constants |
| **D8** | *(later, optional)* Off-screen magnifying-glass bubbles — explicitly OUT of the first cut; separate follow-up, not part of the GO scope. | — | new; `render/camera.py` |

**Sequencing:** D1 → D2 → D3 → D4 form the byte-identical scaffold + framer + coverage, all under
the #1304 gate and safe because camera-off is identity. D5/D6 swap the two throwaway scaffolds for
sourced data and can proceed in parallel once their gates (#789, #790/#661) clear. D7 is a small
constants change once the feel decision lands. D8 is out of scope for the first production camera.

## §6 — Decisions to surface first (this spike surfaces, does not resolve)

Two open `decision:` tickets gate the DEV work; a third decision is newly identified:

1. **#1304 Q1 — build the moving camera vs. stay fixed** (`decision`, OPEN). The master gate:
   nothing in §5 is buildable until this ratifies "build moving." The #1315 GO is its felt evidence.
   → Next action: `guide-human-decision` on #1304, informed by this decomposition.
2. **#789 — KO-in-world decouple value model** (`decision`, `deferred`, OPEN). Gates **D5**; the
   camera consumes its world-coordinate decouple. → `guide-human-decision` on #789 (separate claim).
3. **#1331 — feel-number values** (`decision`, `area:display`, OPEN; filed by this spike). Zoom-in
   cap (#1315 held 1.8×), zoom-out ceiling (~0.52× derived from CamLimit), pan/zoom ease rates
   (0.07 / 0.05). Per RULES → "Changing values" these need a designer decision or a citation, not
   game-feel alone. Ratified **as its own ticket** — not folded into #1304 — so any number change is
   set intentionally under human supervision (owner decision, 2026-08-08). Gates **D7**.

A **keep-a-fixed-camera-mode toggle** is *not* a blocking decision: the identity default already
provides it for free (camera off = today's fixed view), so shipping the toggle is inherent to the
design, not an open question.

## Recommendation & closure

**Ready to decompose** — the 8 DEV microtasks in §5 are the scoped output, gated as marked. Do
**not** file the DEV children yet: D1–D4 wait on #1304 ratifying "build moving," D5/D6 wait on
#789 / #790, and D7 waits on **#1331**. Run `guide-human-decision` on **#1304**, **#789**, and
**#1331** next (each its own claim); file the DEV children downstream of those rulings, one at a
time.

## Cross-refs

- **#1315** — throwaway prototype GO + findings (`docs/research/2026-08-07-camera-prototype-experiment-findings.md`); preserved branch `br-elderberry/pycats-1315-spike-throwaway-follow-zoom-camera` (unmerged).
- **#1279** — code-verified Melee/Brawl/PM camera study.
- **#790** — datamined PM FD CamLimit/Dead floats.
- **#1304** — ARC/decision: how pycats builds its in-battle camera (Q1 = fixed vs. moving).
- **#1331** — decision: camera feel-number values (zoom caps + ease rates); filed by this spike, gates D7.
- **#789** — KO-zone decision (shares the decouple-from-screen prerequisite).
- **#45** (CLOSED) — foundational screen/camera sizing (Q4 sketch). **#80** (CLOSED) — world-unit rendering research (not a camera prerequisite).
- **#661** — per-stage stages epic (home for CamLimit/Dead stage data). **#734** — off-screen damage.
- Pipeline landmarks: `BattlePresenter.show` (`sim/presenters.py`); `DisplayManager.present` (`shell/display_manager.py`); `Fighter._outside_blast_zone` (`entities/fighter.py`); `config/stage.py`.
