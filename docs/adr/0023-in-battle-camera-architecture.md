# ADR-0023 — In-battle camera architecture: auto-pan/zoom viewport

- **Status:** Accepted  *(2026-08-08 — owner ruling on #1304, in a guide-human-decision + grilling session, ELDERBERRY)*
- **Date:** 2026-08-08

## Context

pycats has no camera today: the battle renders at a fixed 960×540 and blast zones are hard-coupled
to the screen (`Fighter._outside_blast_zone`, `screen ± BLAST_PADDING`; #45). The throwaway
prototype #1315 play-tested an auto follow+zoom camera and returned **GO** — the owner played it
live and approved the feel (`docs/research/2026-08-07-camera-prototype-experiment-findings.md`).

The primary inputs are two code/data-verified studies: **#1279** (comparative Melee/Brawl/PM camera
study, Melee decomp-verified) and **#790** (datamined PM 3.6 FD `CamLimit`/`Dead` box floats). Their
Q4 finding forces the shape of this decision: **box geometry is sourceable to the integer, but
camera *feel* — zoom speed, smoothing, screen-shake — has no Brawl/PM primary** (it lives behind the
un-decompiled-engine wall, #1279 Q4). So "how faithful can we be" is not a research answer — it is a
design decision, which is why this ADR must precede the #803 build-scoping spike. (#803 in fact ran
ahead, deliberately conditioned on this ruling; its decomposition is gated against these choices.)

The decision was taken as a guide-human-decision + grilling session over five points (Q1–Q5),
each put to the owner one at a time with a recommendation and the #1279/#790/#1315 evidence.

## Decision

**Q1 — Build the moving camera for v1.** Commit to the auto-pan/zoom camera, not a deferred
fixed-only v1. The #1315 GO de-risked it.

**Q2 — Melee-derived bounding-box framer.** Adopt the one family all three source games share and
the prototype already implements: fit the view to the alive fighters' bounding box (+ flat margin) →
clamp zoom-out to the per-stage `CamLimit` box so blast lines never show → pan toward the box center
→ ease per-frame with a lerp. Melee's is the code-verified reference (#1279).

**Q2b — Per-stage parameters.** The camera's box/zoom parameters (`CamLimit` clamp, zoom-in/out
caps) are **per-stage data attached to `Stage` objects** in `pycats/entities/stages.py` (which
already carries a 2-stage registry: Starting Point + Battlefield), sourced from #790 — not global
module constants. The camera reads geometry from the current stage.

**Q3 — Feel/provenance policy (hybrid).** Where a Melee decomp value maps, source it and label it
"Melee-derived, PM feel unverified" (e.g. the zoom-out ceiling already derives from #790's
`CamLimit`; the fit structure from #1279). Where nothing maps (exact ease/lerp rates, any shake),
record it as a game-designer `TUNED` value with a design-doc basis, per RULES → "Changing values"
(ADR-0003). The concrete numbers are ratified separately in **#1331**, which inherits this policy as
its rubric.

**Q4 — KO-in-world decouple sequencing.** Decoupling KO bounds from the screen is a prerequisite
**only** for the step that frames against sourced world-bound KO geometry. The framer, the
camera-off identity default, and the camera tests do **not** touch KO and proceed without it. The
decouple's **value model stays #789's own decision** — this ADR ratifies the sequencing dependency,
not #789's numbers.

**Q5 — Test/determinism policy + default.** The camera is **not** covered by golden screenshots.
Camera correctness is verified by **behavioral + determinism tests** — the framer math (bounding box
over alive fighters, clamp to per-stage `CamLimit`, zoom-in/out caps, per-frame lerp) and a
determinism check (identical sim state → identical camera transform, repeatably) — not by pixel
baselines. The camera is **presentation-only**: it never feeds back into the deterministic sim, so
it cannot perturb physics, KO, or determinism. The **existing fixed-render goldens stay valid** by
pinning the golden/test render to camera-off/identity — they are the fixed-view snapshots, not
camera snapshots. The **live-game default is non-moving** (fixed view); **`K` toggles the moving
camera on**, as the prototype does.

## Consequences

- **#803's decomposition is amended.** Task **D4 ("camera-on golden baselines") is struck** and
  replaced by "camera behavioral + determinism tests (no goldens)." The downstream DEV children
  carry the amended D4; #803's findings doc predates this ruling and is superseded on that point.
- **The prototype code carries across.** The #1315 branch's framer + feel code is the starting
  point; its two throwaway scaffolds are rebuilt — the fake KO distances (`EXPERIMENTAL_WIDE_BLAST`)
  via the #789 decouple (D5), and the missing coverage via behavioral tests (amended D4).
- **A per-stage camera-data seam is added** to `pycats/entities/stages.py` (a new field on `Stage`),
  populated for Starting Point + Battlefield from #790's floats. Adding stages later (#661) adds
  rows, not camera code.
- **Feel numbers are gated on #1331**, which now has this hybrid policy as its adjudication rubric;
  no camera constant lands without that ruling (owner-supervised, per the owner's #1331 intent).
- **The golden render must force camera-off** as an invariant; today's non-moving default already
  satisfies it, and a future on-by-default change would still pin the golden render off.
- **Easier after this:** the DEV children can be filed against a settled architecture; the framer,
  the identity default, and the tests are all independent of the #789 dependency and can start once
  the children are filed. **Harder:** introduces the per-stage data seam and a #789 dependency
  before full KO faithfulness is reached.
- **Ruled out for v1:** off-screen magnifying-glass bubbles (#734) and Melee's per-count weight
  table — deferred, matching #1315/#1308.

## Refs

Decision #1304 (this ADR). Scoping spike #803
(`docs/research/2026-08-08-pm-camera-follow-zoom.md`, decomposition D1–D8, D4 amended here).
Prototype #1315 (GO — `docs/research/2026-08-07-camera-prototype-experiment-findings.md`; preserved
branch `br-elderberry/pycats-1315-spike-throwaway-follow-zoom-camera`, unmerged). Source studies
#1279 (Melee decomp) and #790 (datamined FD `CamLimit`/`Dead` floats). Related decisions #789
(KO-in-world value model) and #1331 (camera feel-number values). Foundational #45 (camera sizing),
#80 (world-unit rendering). Tuning-provenance policy ADR-0003.
