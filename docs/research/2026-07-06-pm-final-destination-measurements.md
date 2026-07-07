# Project M Final Destination measurements — for a v1 FD stage (#659)

> **Role:** RESEARCH · `area:entities` · closes #659 · unblocks the v1 FD-stage DEV ticket.
> **Date:** 2026-07-06 · **Agent:** BANANA
> **Method:** targeted web research; every numeric claim carries its source verbatim or is
> flagged **⚠ best-guess** with reasoning (RULES → "Read the source before asserting" / #562).
> No PM-mechanic value is stated as "confirmed" from inference.

## TL;DR

1. **No open web source publishes PM 3.6 (or Brawl) FD's blast-zone / ledge numbers in
   quotable form.** SmashWiki and the PM-official site describe FD only *qualitatively*
   ("Large size, Medium ceiling, Medium blast zones"). The real floats live inside the stage
   `.pac` (Brawl/PM: `Dead0N`/`Dead1N` + camera bones) — reachable only by a datamining dump,
   the same engine-file wall noted for air-dodge velocity.
2. **The one quotable primary numeric anchor is *Melee* FD**, datamined into libmelee's source.
   PM restored Melee-style physics, so Melee FD is the defensible proportional basis for a v1 —
   but it is **Melee, not PM**; PM's Brawl-based FD differs, so the pixel numbers below are a
   **⚠ best-guess v1 spec**, not sourced PM values.
3. **Answer to the unit→px question (the deliverable's crux): FD's real proportions do *not*
   fit a fixed 960×540 1:1.** At pycats' fighter scale (`PX_PER_UNIT ≈ 5.4`) the FD **ground
   fits fine (~924 px wide)**, but the **blast zones land ~848 px *beyond* each screen edge**
   (and ~1015 px above / ~756 px below). pycats has a fixed, non-scrolling camera and currently
   models KO with `BLAST_PADDING = 50 px` beyond the screen — ~17× closer than a faithful FD.
   **Reconciling the ground-scale vs blast-zone-scale tension is a `decision:` (surfaced here,
   not decided).**
4. **Ticket "Have" correction:** #659 says "blast zones aren't modelled explicitly." They *are* —
   `Fighter._outside_blast_zone()` KOs at `BLAST_PADDING = 50 px` beyond each of the four screen
   edges (`pycats/config.py`, provenance `BLAST_PADDING`, TUNED under #584, "no canon"). The v1
   FD work is a *re-scaling / re-siting* of an existing boundary, not a from-scratch model.

## Termination checklist (each required measurement, sourced or ⚠)

| # | Measurement | Value | Grounding |
|---|---|---|---|
| 1 | FD ground full width | **171.13 Melee units** → ⚠ **~924 px** at 5.4 | libmelee edge consts (sourced, Melee) |
| 1 | Ledge / edge x (grab point) | **±88.47 units** hang, **±85.57** teeter | libmelee (sourced, Melee) |
| 1 | Surface y | pycats-defined, not PM-derived | see §5 recommendation |
| 2 | Blast zones L/R/T/B | **−246 / +246 / +188 / −140 units** | libmelee (sourced, Melee) |
| 3 | Ledge geometry (lip overhang) | hang is **2.9 units (~16 px) outboard** of teeter | derived from the two libmelee consts |
| 4 | Unit → px scaling | **5.4 (ground fits; blast zones off-screen)** | pycats `PX_PER_UNIT`; **flag `decision:`** |

## Primary sources & what each does / does not carry

- **libmelee `melee/stages.py`** (github.com/altf4/libmelee) — datamined Melee constants, the
  cleanest *quotable* numeric source. Verbatim for `FINAL_DESTINATION`:
  - `BLASTZONES … : (-246, 246, 188, -140)` — format **(left x, right x, top y, bottom y)**.
  - `EDGE_POSITION … : 88.4735488892` (the x where a fighter grabs/hangs the ledge).
  - `EDGE_GROUND_POSITION … : 85.5656967163` (the x where a fighter teeters on the ground edge).
  - No side platforms (`left_/right_platform_position()` return `(None, None, None)`).
  - Stage is symmetric about **x = 0**; the left edge is "always the same, but negative."
  - **Caveat:** these are **Melee** world units. libmelee does not cover Brawl/PM stages.
- **20XX-Melee-Hack-Pack `SSBM Facts.txt`** — confirms the *structure*: a stage carries a blast
  quadruple as floats. Verbatim:
  > `0x0074 float Blastzone left` · `0x0078 float Blastzone right` ·
  > `0x007C float Blastzone top` · `0x0080 float Blastzone bottom`
- **OpenSA STDT wiki** + **BrawlBox stage-editing docs** — how Brawl/PM (the base for PM 3.6)
  store the same thing: the death boundary lives in the stage `.pac` `modeldata` `stageposition`
  as **`Dead0N`** (top/left corner) and **`Dead1N`** (bottom/right corner) bones; camera bounds
  are separate camera bones. **No FD-specific float values are published** — you must open
  `STGFINAL.pac` in BrawlBox (or parse with brawllib_rs) to read them. *(OpenSA host was
  unreachable at research time; the `Dead0N/Dead1N` mechanism is quoted from the BrawlBox
  stage-editing thread surfaced in search, not the primary wiki.)*
- **SmashWiki FD pages (SSBM / SSBB / disambiguation)** — **prose only, zero numbers.** Brawl FD
  is described only as "somewhat smaller [than Melee], … ceiling is somewhat lower," with "stage
  lips" that catch recoveries. Useful as *direction* (Brawl/PM FD ≈ Melee FD, a touch smaller /
  lower ceiling), not as values.
- **pmunofficial.com FD page** — PM-official, **qualitative only**: FD is **size "Large",
  0 platforms, ceiling "Medium", side blast zones "Medium"**, with a "unique curved underside"
  that lets you sweetspot the ledge by riding the wall (and a lip that blocks tether-from-under).

**Net:** the exact PM 3.6 FD floats are **⚠ not sourceable from the open web** — they require a
`STGFINAL.pac` (PM/Project+) datamining dump. That follow-up is named in §6.

## The grounded proportions (scale-independent — the transferable finding)

From the Melee FD anchor, relative to the **ground half-width** (teeter edge, 85.57 u):

| Boundary | Units | Ratio to ground half-width |
|---|---|---|
| Ledge grab (hang) | 88.47 | **1.034×** (lip overhangs the teeter edge by ~3 u) |
| Side blast zone | 246 | **2.875×** |
| Ceiling (top blast) | 188 | **2.197×** |
| Floor (bottom blast) | 140 | **1.636×** |

Two feel-relevant facts fall out: the **ceiling (188) is farther than the floor (140)** — easier
to KO downward (spike) than upward — and the **ledge lip sits ~3 u outboard of the teeter edge**,
the overhang that makes sweetspotting/edge-hogging work (cross-ref pycats `LEDGE_CATCH_W/H`).

## Unit → pixel mapping at pycats' scale (the crux)

Using pycats' fighter scale `PX_PER_UNIT ≈ 5.4` (from `docs/research-120-smash-units-and-sources.md`),
960×540 screen, center x = 480:

| Element | px from center | On the 960×540 screen? |
|---|---|---|
| Ground full width | **924 px** | ✅ fits (≈18 px margin each side) |
| Teeter edge | ±462 px → x = 18 / 942 | ✅ on-screen |
| Ledge grab (hang) | ±478 px → x = 2 / 958 | ✅ (right at the edges) |
| **Side blast** | **±1328 px → x = −848 / +1808** | ❌ **~848 px off each edge** |
| **Ceiling** | **1015 px above** | ❌ far above the 540-tall view |
| **Floor** | **756 px below** | ❌ far below the view |

**Reading:** a scale that makes fighters and the FD ground correctly sized (5.4) necessarily
throws the blast zones far off a fixed screen — which is *normal Smash* (blast zones are off-camera;
the real game zooms/pans). pycats has **no scrolling/zooming camera**, so it can't honor both
"ground fills the screen" and "faithful blast-zone distance" at once. Its current compromise —
`BLAST_PADDING = 50 px` beyond the screen — is ~17× tighter than faithful (~848 px), i.e. a
deliberate fixed-camera compression, not a bug.

Note the scale tension with the *current* arena too: pycats' `THICK_PLAT_WIDTH = 800 px` implies
`800 / 171.13 ≈ 4.68 px/unit`, below the fighter scale of 5.4. Adopting 5.4 for FD widens the
ground to ~924 px (keeps fighters correctly sized relative to the stage); keeping 800 px would
shrink fighters-vs-stage. The v1 should pick 5.4 for consistency and let the ground be ~924 px.

## Recommendation — a v1 FD spec + one decision to escalate

**Buildable now (⚠ best-guess, Melee-proportioned, pycats-scaled — not sourced PM values):**

- **Ground platform:** width **≈ 924 px** (2 × 85.57 u × 5.4), centered on x = 480 → spans
  x ≈ 18 … 942. (Or round to a clean **920 px**.)
- **Ledge grab x:** the ground's left/right edges, with the grab lip **~16 px outboard** of the
  visual edge (the 2.9-u overhang × 5.4) — reuse the existing `LEDGE_CATCH_W/H` box at those corners.
- **Surface y:** **pycats-defined, no PM basis** — keep the current stage-surface convention
  (`SCREEN_HEIGHT − THICK_PLAT_Y_OFF − GLOBAL_Y_OFF`) so fighters spawn/land where they do today;
  FD only changes width + platform count (0 side platforms), not the floor height.
- **Blast zones:** **do not hard-port ±246/±188/−140 to px** — they don't fit. Keep the existing
  four-edge `BLAST_PADDING` model for v1 unless the decision below rules otherwise.

**Escalate as a `decision:` (per RULES "Changing values" — surfaced here, not decided):**

> **How should pycats reconcile faithful FD blast-zone distance with its fixed 960×540 camera?**
> Options: (A) keep `BLAST_PADDING`-style near-screen KO (unfaithful distance, but the whole
> fight stays on-screen — current behavior); (B) adopt faithful off-screen blast distances
> (~848 px side / ~1015 up / ~756 down) and accept KOs happening off the visible screen, or add
> a camera; (C) pick a *lower* scale so blast zones sit near the screen edge, shrinking the ground
> and fighters proportionally. This is a game-feel / camera-model call with no canonical answer —
> it needs a game-designer decision or a ratified `decision:` ticket, not a guessed number.

## Out of scope (per #659)

Implementing the stage (the v1 FD-stage DEV ticket this unblocks); stage-selection; ratifying
the scale/camera decision above (surfaced, not decided).

## Follow-ups (named, not filed — one-at-a-time downstream)

1. **v1 FD-stage DEV ticket** — build the ~924 px ground / 0-platform FD from this spec (already
   anticipated by #659; #660 per the dispatch).
2. **`decision:` — FD blast-zone vs fixed-camera reconciliation** (the escalation above).
3. **Optional datamining spike** — read the real PM 3.6 / Project+ `STGFINAL.pac` `Dead0N/Dead1N`
   + camera bones (BrawlBox / brawllib_rs) to replace the ⚠ Melee-proportioned numbers with
   sourced PM floats, *if* exact PM fidelity is wanted over Melee-proportioned feel.

## Refs

pycats current stage: `pycats/game.py` (inline `Platform(...)`), `pycats/config.py`
(`THICK_PLAT_DICT` / `THIN_PLAT_DICT_L/R`, `LEDGE_CATCH_W/H`, `BLAST_PADDING`),
`pycats/entities/platform.py`, `pycats/entities/fighter.py` (`_outside_blast_zone`).
Scale basis: `docs/research-120-smash-units-and-sources.md` (`PX_PER_UNIT ≈ 5.4`).
Provenance: `BLAST_PADDING` / `LEDGE_CATCH_*` (TUNED, #584). Grounding rule: RULES → "Read the
source before asserting" (#562). Sources: libmelee `melee/stages.py`; 20XX `SSBM Facts.txt`;
OpenSA STDT wiki; BrawlBox stage-editing docs; SmashWiki FD (SSBM/SSBB); pmunofficial.com FD.
