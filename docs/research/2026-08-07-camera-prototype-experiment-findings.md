# Camera prototype experiment — go/no-go findings (#1315)

> **Agent:** ELDERBERRY · **Authored:** 2026-08-07 · **Ticket:** #1315

Result of the throwaway follow+zoom camera play-test ratified in #1308
(`docs/design/camera-prototype-experiment-spec.md`). This is the closing artifact of the
spike and the felt-evidence input to **#1304 Q1** (does pycats build a moving camera for v1,
or stay fixed?).

## Recommendation: **GO**

The moving-camera concept passes the play-test. The human played the throwaway live and
approved the feel. **Recommend #1304 Q1 = build the auto follow+zoom camera** (moving, not
fixed), productionized via the scoping spike **#803**. Nothing structural blocked it.

## Method

Per the ratified spec: the human played the prototype **live** (no video), toggled the camera
on/off with `K`, and gave a **binary go/no-go**. Judged the three ratified scenarios — neutral
1v1, launch toward the blast zone, max spread ↔ max stack — against today's fixed view.

## What was judged, and the verdict

- **Feel: approved.** Initial pan/zoom read as slightly quick; the human asked for slower
  motion with more delay. Delivered by lowering the per-frame ease (pan lerp 0.07, zoom lerp
  0.05, zoom trailing pan) and re-judged — approved.
- **Zoom range eyeballed** (via the in-battle dev readout of live zoom + camera center):
  zoom-**in** cap held at **1.8×**; zoom-**out** ceiling **~0.52×**, which is now **derived
  from the sourced CamLimit box** (#790), not a by-feel guess — and it corroborated the
  earlier by-feel 0.55. **Final feel numbers are deferred to productionization**, per the spec
  (the experiment answers the concept, not the exact constants).
- **Stage-always-visible: solved the PM-faithful way.** Clamping the camera pan + zoom-out to
  the sourced **CamLimit** box (inner) keeps the stage framed with no explicit visibility
  check — it falls out of the clamp. Verified against the multi-fighter bounding box (the
  framer already boxes all alive fighters, so it generalizes past 2).

## Structural findings (why nothing blocked GO)

- **Camera-off is byte-identical.** The render-parity oracle + golden snapshots stay green
  (2277 passed, 1 xfailed) with the camera off — the identity-default requirement holds, so a
  production camera can ship behind an off-by-default flag without disturbing existing pixels.
- **The two throwaway scaffolds are replaceable, not blockers** (both flagged in the spec):
  1. the **fake ±848/745/486 px KO distances** (`EXPERIMENTAL_WIDE_BLAST`) → replaced in
     production by the KO-in-world-coordinates decouple (**#789** governs the value model);
  2. **no camera-on golden coverage** → production adds golden baselines for the camera-on
     path (camera-off stays identity, so existing goldens hold).

## Zone model confirmed (sourced)

The camera works against two per-stage boxes, both datamined in **#790** (PM 3.6 FD, at
`PX_PER_UNIT ≈ 5.4`):

| Box | Role | Beyond each screen edge (L/R · top · bottom) |
|-----|------|----------------------------------------------|
| **CamLimit** (inner) | camera pan-limit — on-screen boundary | +438 · +346 · +162 px |
| **Dead** (outer) | KO / blast boundary | +848 · +745 · +486 px |

Between them is the off-screen / magnifying-glass band (the bubble is cut from this
throwaway). The `--dev` overlay draws both boxes as outline-only rects on the background and
relaxes the clamp to Dead so all three zones are visible for tuning.

## Productionization scope (hand to #803 → a new DEV ticket)

Approval green-lights **building it for production**, not shipping the throwaway. The framer +
feel code carries across; the productionization pass must:

1. Replace the fake KO distances with the **KO-in-world-coordinates decouple** (#789 value
   model), so the camera frames against sourced world-bound KO geometry, not a hardcoded box.
2. Add **camera-on golden baselines** (camera-off stays identity).
3. Formalize **CamLimit / Dead** as per-stage **stage data** (the PM `.pac` bones), not
   module constants.
4. Finalize the **feel numbers** (zoom-in/out caps, ease rates) as a game-designer decision or
   sourced values, per RULES → "Changing values".

## Artifacts

- **Prototype code** (throwaway, **not merged**): preserved on origin branch
  `br-elderberry/pycats-1315-spike-throwaway-follow-zoom-camera` (commits `97430a1`,
  `acde223`, `274b447`). Camera default OFF; toggle `K`; `--dev` draws the zone overlay.
- **This findings note** — the durable output on main.

## Cross-refs

- **#1304** Q1 (fixed vs. moving) — this GO is the felt evidence to resolve it.
- **#1308** — the ratified experiment spec (`docs/design/camera-prototype-experiment-spec.md`).
- **#803** — production scoping spike (owns the productionization pass).
- **#789** — parked blast-zone value model (the fake KO distances do not touch it).
- **#790** — datamined PM FD `CamLimit`/`Dead` floats.
- **#1279** — source-game camera study (`docs/research/2026-08-07-camera-melee-brawl-pm-comparison.md`).
