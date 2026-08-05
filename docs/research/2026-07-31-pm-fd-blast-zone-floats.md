# PM 3.6 Final Destination blast-zone floats — datamined from `STGFINAL.pac` (#790)

> **Role:** RESEARCH · `area:entities` · closes #790 · **unblocks decision #789** (blast-zone
> value model; owner ruled Option 2 "PM-faithful/scaled" on 2026-07-20 — these sourced floats
> are the required input to picking the scale).
> **Date:** 2026-07-31 · **Agent:** ELDERBERRY
> **Method:** direct datamine of the stage `.pac` bone data — tool output verbatim, no inference
> on the numbers. Every float below is read by `scripts/datamine_stage_bounds.py` and reproducible
> (§Reproduce). Inference is confined to §Interpretation and is labelled.

## TL;DR

1. **PM 3.6 FD's authored blast (KO) zone = `(-246, +246, +188, -140)` units** (left / right /
   top / bottom), read from the `Dead0N`/`Dead1N` bones of PM's `STGDXFINAL.pac`. This is
   **exactly** the Melee FD blast quadruple libmelee publishes — the value #659 used as its
   ⚠ "Melee-proportioned guess." **So #659 was not guessing: PM 3.6 literally ships Melee's FD
   blast zones.** The guess is now a *sourced PM value*, corroborated by two independent datamines
   (libmelee's Melee stage table + this PM stage-bone read) agreeing to the integer.
2. **Camera pan-limit ≠ blast zone.** PM FD's `CamLimit0N`/`CamLimit1N` = `(±170, +114 / -80)` —
   a *separate, tighter* boundary (the camera's pan limit), distinct from the KO boundary. pycats'
   `Fighter._outside_blast_zone` maps to the **`Dead`** (KO) bones, **not** `CamLimit`. pycats has
   a fixed, non-scrolling camera, so `CamLimit` has no pycats analogue (it would only matter once
   the camera decouples — #788's horizon work).
3. **The unit→px crux is confirmed with sourced numbers.** At `PX_PER_UNIT ≈ 5.4`, PM FD's blast
   zones sit **~848 px beyond each 960-wide screen edge**, ~745 px above the screen top and
   ~486 px below the screen bottom — the exact figure #659 derived, now sourced rather than
   proportioned. A faithful PM FD blast box **does not fit** a fixed 960×540 camera; the current
   `BLAST_PADDING = 50` / `BLAST_PADDING_X = 100` is a ~17× compression by feel. This is the input
   #789 Option 2 needs to pick a principled scale ratio.
4. **Tooling finding:** the existing `brawllib_rs` datamine (fighter-animation path) **cannot** read
   stage params — it panics on any stage `.pac`. A **new pure-stdlib extractor**
   (`scripts/datamine_stage_bounds.py`) reads stage boundary bones without brawllib and is the
   repeatable path for future stages (§Reproduce, §Tooling).

## Sourced floats (tool output, verbatim)

Boundary bones, **local (authored) translate**, in stage/world units. `*0N` = top-left corner
(min x, max y); `*1N` = bottom-right (max x, min y). Full run in §Reproduce.

| Bone | Role | **PM 3.6** (`STGDXFINAL`) | Brawl base (`STGFINAL`) |
|------|------|---------------------------|--------------------------|
| `Dead0N`   | blast/KO top-left (x, y)     | **(−246, +188)** | (−240, +180) |
| `Dead1N`   | blast/KO bottom-right (x, y) | **(+246, −140)** | (+240, −115) |
| `CamLimit0N` | camera top-left (x, y)     | (−170, +114) | (−180, +130) |
| `CamLimit1N` | camera bottom-right (x, y) | (+170, −80)  | (+180, −60)  |
| `Player1N..3N` | spawn points (x)         | 60 / −20 / 20 | 60 / −20 / 20 |
| `Rebirth1N..3N` | respawn-platform pts    | (−50,45)/(50,45)/(−16,45) | (0,50)×3 |

**Blast quadruple (L, R, T, B):**
- **PM 3.6 FD: `(-246, +246, +188, -140)`** ← the deliverable.
- Brawl FD: `(-240, +240, +180, -115)` (base, for reference — PM widened the box slightly and
  dropped the floor deeper).

**Provenance of the "Melee match":** libmelee `melee/stages.py`
`FINAL_DESTINATION … BLASTZONES: (-246, 246, 188, -140)` (datamined Melee constants, quoted in
#659). PM's `Dead` bones equal it to the integer.

## Interpretation (labelled — not part of the raw read)

**Why "local" and not "world."** Each MDL0 bone header carries both a local translate and a
precomputed world-transform matrix. For PM's `Dead`/`CamLimit`/`Rebirth` bones the two **disagree**
(e.g. `Dead0N` local `(-246, 188)` vs world `(-185, 220)`). The world column is a **stale artifact**,
not a real parent transform: PM's `Rebirth2N` and `Rebirth3N` have *distinct* locals `(50, 45)` and
`(-16, 45)` yet carry *identical* world `(0, 20)` — impossible under any real bone hierarchy, so the
precomputed matrices were simply not rebuilt after PM edited the local translations in BrawlBox. The
**local translate is the authored value**; the Brawl base (unedited) confirms this with
`local == world` on every bone. The `Dead`-bone locals matching libmelee's published Melee floats
exactly is the independent corroboration. *(Open question, low-stakes: whether the retail PM engine
reads a bone's local or a composed world position at stage load. It cannot change this answer — a
non-identity parent would have to reproduce Melee's exact published floats by coincidence — but a
future spike could confirm against the PM stage-loader code.)*

**Unit→px, restating the #659 crux with sourced numbers** (`PX_PER_UNIT ≈ 5.4`, screen 960×540 so
half-width 480 px, half-height 270 px; stage symmetric about x=0):

| Quantity | PM units | px (×5.4) | vs fixed 960×540 |
|---|---|---|---|
| Blast left/right | ±246 | ±1328 px | **~848 px beyond** each screen edge |
| Blast top | +188 | 1015 px up | ~745 px above screen top |
| Blast bottom | −140 | 756 px down | ~486 px below screen bottom |
| Ledge (teeter edge, from #659) | ±85.57 | ±462 px | fits (ground ~924 px wide) |
| Camera pan limit L/R | ±170 | ±918 px | beyond screen, but it is the *camera* bound |

So the **ground fits** the screen (~924 px ≤ 960) but the **blast box is ~2.8× the screen width** —
the ground-scale-vs-blast-scale tension #659 flagged, now on sourced PM numbers. Blast-to-ledge
gap: `(246 − 85.57) = 160.4 u ≈ 866 px` of off-stage space per side in faithful PM.

## Feeding #789

- **Option 1 (screen-relative, tuned by feel):** unaffected by these numbers — it explicitly
  abandons faithfulness.
- **Option 2 (scaled-to-fit fraction of the faithful distance):** this doc supplies the faithful
  distances. A compression ratio `r` applied to the sourced blast distances gives the ratified
  padding: e.g. side padding `= r × 848 px` beyond the screen edge (`r ≈ 0.12` reproduces today's
  `BLAST_PADDING_X = 100`; `r ≈ 0.06` reproduces the vertical `BLAST_PADDING = 50`). Picking `r`
  is the owner's ruling; the sourced anchors are now available.
- **Option 3 (explicitly interim):** these numbers are the "faithful values" it would defer to.

Not decided here — this is the research input, per the #789 split. `BLAST_PADDING` /
`BLAST_PADDING_X` remain as-is until #789 rules.

## Tooling — why the fighter datamine couldn't do this

`brawllib_rs` (the #614/#753 datamine used for fighter animation lengths) **panics on stage pacs**:

- Its `arc::arc()` hardcodes the fighter assumption that **ARC child-0 is a `Sakurai` moveset
  block** (`"" if i == 0 => ArcChildData::Sakurai(...)`). A stage's child-0 is not, so it reads a
  garbage offset — panic, backtrace at `brawllib_rs::sakurai::arc_sakurai`.
- It only decompresses a **whole-file** top-level compression, never **per-child** compression.
  Stage pacs store each ARC child **LZ10-compressed** (Nintendo LZ77 type `0x10`), so even past the
  Sakurai bug the model data is compressed bytes brawllib never inflates.

Both walls are why #659 could not source these floats and flagged BrawlBox as the fallback. The new
extractor sidesteps brawllib entirely (pure stdlib): parse the `ARC`, LZ10-decompress each child,
scan the decompressed nested ARC for MDL0 bone headers (layout taken verbatim from brawllib's
`mdl0/bones.rs`), read each boundary bone's translate. No BrawlBox / GUI needed.

## Reproduce

`.pac` files are copyrighted and never committed. Point the extractor at a local dump:

```
cd <pycats>
PM=repros/pm36-codeset/extracted/projectm/pf/stage/melee/STGFINAL.pac     # PM 3.6 FD (STGDXFINAL)
BR=~/Documents/Study/Rust/pm-data/brawl-dump/DATA/files/stage/melee/STGFINAL.PAC   # vanilla Brawl FD
python3 scripts/datamine_stage_bounds.py "$PM" "$BR"
```

Full PM output (verbatim):

```
=== .../STGFINAL.pac  (internal name: STGDXFINAL, 2607264 bytes) ===
  bone          local x   local y  local z      world x   world y  world z
  CamLimit0N    -170.00    114.00     0.00      -160.00    180.00     0.00
  CamLimit1N     170.00    -80.00     0.00       160.00   -120.00     0.00
  Dead0N        -246.00    188.00     0.00      -185.00    220.00     0.00
  Dead1N         246.00   -140.00     0.00       185.00   -180.00     0.00
  Player1N        60.00      0.00     0.00        60.00      0.00     0.00
  Player2N       -20.00      0.00     0.00       -20.00      0.00     0.00
  Player3N        20.00      0.00     0.00        20.00      0.00     0.00
  Rebirth1N      -50.00     45.00     0.00       -50.00     45.00     0.00
  Rebirth2N       50.00     45.00     0.00         0.00     20.00     0.00   # world stale (see Interpretation)
  Rebirth3N      -16.00     45.00     0.00         0.00     20.00     0.00   # world stale
```

(`Player4N`/`Rebirth4N` absent — FD is a ≤3-spawn Melee-derived layout; the extractor prints
`(not found)` for absent bones rather than inventing a value.)

## Out of scope

Implementing/tuning the blast padding (the #789 decision + downstream DEV); confirming
local-vs-world at the PM engine level (labelled open question above); non-FD stages (the extractor
handles them — just pass another `.pac`).

## Cross-refs

Unblocks #789 (KO-zone value ratification); supersedes the ⚠ guess in #659
(`docs/research/2026-07-06-pm-final-destination-measurements.md`) by sourcing the same numbers;
`config.BLAST_PADDING` / `config.BLAST_PADDING_X` / `Fighter._outside_blast_zone`;
extractor `scripts/datamine_stage_bounds.py`; brawllib datamine env (#614/#753).
