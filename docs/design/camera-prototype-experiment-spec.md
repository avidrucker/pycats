# Camera prototype experiment — ratified spec (#1308)

> **Agent:** ELDERBERRY · **Authored:** 2026-08-07 · **Ticket:** #1308

Ratified design for a **throwaway follow+zoom camera prototype** whose play-test produces a
**go/no-go** feeding **#1304 Q1** (does pycats build a moving camera for v1, or stay fixed?). Grilled
into shape with the human designer on 2026-08-07. The experiment is **run** under **#1315**; this doc
is the authoritative spec that ticket builds to.

## Why an experiment (not a straight decision)

#1279 (`docs/research/2026-08-07-camera-melee-brawl-pm-comparison.md`) Q4 is the reason: camera
**feel** — zoom speed, smoothing, screen-shake — is **unsourceable** (Brawl's engine is
un-decompiled; the same wall as the smash-charge-cap global #637/#638). No source can say whether a
PM/Brawl-style moving camera *feels good in pycats*; only a throwaway you can play can. But a prototype
with no design drifts or measures nothing — so the experiment was designed first (this doc), then a
tight build pass runs it (#1315).

## The ratified decisions

| # | Decision | Ruling |
|---|---|---|
| Judge | How we decide | **Human plays it live** and gives go/no-go. **No video capture.** A canned sim may be added with a run command, but the human at the keyboard is the judge. Outcome is **binary: full moving camera (follow + zoom) vs. fixed.** |
| Scope | What is built | **In:** fighters' bounding box · fixed margin · zoom-to-fit + zoom-in/out clamps · pan-to-center · per-frame smoothing (lerp on pan + zoom) · **camera on/off toggle key**. **Out:** Melee per-count weight table `{1.5, 1.32, 1.16, 1.0}` (use one flat margin) · magnifying-glass bubble (known gap). |
| World-bound | KO room for the camera to follow into | Throwaway swaps the 3 KO paddings in `Fighter._outside_blast_zone` for the big **sourced** PM/Melee FD distances — **~848 px** side, **~745 px** top, **~486 px** bottom (from #789's table at `PX_PER_UNIT = 5.4`). Screen-relative model kept. **Does not touch #789.** |
| Scenarios | What is play-tested | (1) neutral 1v1 · (2) launch toward the blast zone · (3) max spread ↔ max stack. 4-cat crowd dropped (pycats caps at 2 on-screen; "max spread" already exercises max zoom-out). One canned launch sim **only if time allows**. |
| Branch fate | Where the code lives | Branch pushed to origin, camera **default OFF** (identity = today's pixels), **not merged**. Only durable output on main otherwise: a short findings note feeding #1304 Q1. **If the human approves the feel → merge via a productionization pass** (below), not a raw fast-forward. |
| Timebox | Build cap | **15-min checkpoint** (reassess scope if not yet playable), **30-min hard cap** (judge whatever exists). Forces the cheap oversized-surface transform; the canned sim is cut first if tight. |

## Implementation seam (facts, as of 2026-08-07)

- **`pycats/render/battle.py::render_battle(surface, players, platforms)`** is the sole battle draw
  site; every fighter/platform/attack draws at `p.rect` / `a.rect` in **screen == world** coords today.
  Identity transform = today's pixels byte-for-byte.
- **`pycats/entities/fighter.py::_outside_blast_zone`** KOs on screen edges: L/R at `±BLAST_PADDING_X`
  (100), top `BLAST_PADDING_TOP` (150), bottom `BLAST_PADDING` (50). `PX_PER_UNIT = 5.4`.
- **Cheap transform** (to fit 30m): render the world onto an oversized surface using the existing draw
  code unchanged, then blit a camera-selected sub-rectangle scaled to the 960×540 window — do **not**
  thread a `(scale, offset)` through every draw call.

## Go / no-go bar

- **Green → recommend building the moving camera as a production feature** (hand to scoping spike #803): framing reads
  PM-like and legible, **and** nothing structural blocks it — KO stayed correct behind the hacked
  world-bound, framerate held, identity-default reproduced today's pixels.
- **Kill → fixed camera wins for pycats v1:** it feels worse/disorienting than the fixed view, **or** a
  structural blocker surfaces (the decouple is far larger than a hack; combat tuning reopens badly).
- The experiment answers go/no-go on the **concept only** — it does **not** nail final feel numbers
  (zoom speed, ease constant). That is a later job if it goes green.

## What "merge if approved" means (productionization pass)

Approval is a green light to build it for production, **not** to ship the throwaway hacks. Two pieces cannot
ride a merge as-is and get redone on the way in (scoped by #803):

1. **World-bound hack** → replaced by the KO-in-world-coordinates decouple (#789 governs the value
   model). Merging the fake ~848 px distances as live KO would ship a fake blast zone and step on the
   parked #789.
2. **Golden baselines** → camera-*on* changes pixels, so a production merge adds golden snapshots for
   the camera-on path (camera-*off* stays identity, so existing goldens hold).

The part the human is judging — the **framer + feel** code — carries straight across; only these two
scaffolds are rebuilt properly.

## Cross-refs

- **#1315** — runs this experiment (the build pass).
- **#1304** — the umbrella camera decision this feeds (Q1 fixed vs. moving).
- **#1279** — source-game camera study (`docs/research/2026-08-07-camera-melee-brawl-pm-comparison.md`);
  Q4 is why feel needs a play-test.
- **#803** — production scoping spike (owns the productionization pass if approved).
- **#789** — parked blast-zone value model (the world-bound hack does not touch it).
- **#45** — `docs/research/screen-camera-sizing-findings.md`: camera is a presentation-only,
  golden-affecting viewport layer; identity-default keeps snapshots valid.
