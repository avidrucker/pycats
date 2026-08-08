# In-battle camera — Melee vs Brawl vs Project M (comparative findings) (#1279)

> **Role:** RESEARCH · `area:display` · closes #1279 · **feeds build-scoping spike #803**
> (which defers to this ticket for the source-game camera behaviour + the Melee comparison).
> **Date:** 2026-08-07 · **Agent:** ELDERBERRY
> **Method:** web + decomp research across three parallel source sweeps (one per game).
> **Melee is code-verified** — every Melee code claim is byte-verbatim from `doldecomp/melee`
> `src/melee/cm/camera.c` + `cm/types.h` (branch `master`, fetched 2026-08-07). **Brawl & PM are
> data-verified + qualitative** — Brawl's engine is un-decompiled, so those claims rest on
> per-stage `.pac` bone data (incl. pycats' own datamine, #790), SmashWiki, and community
> reverse-engineering; every value is quoted verbatim or flagged **⟨inference⟩**. This is a
> comparative *mechanics* study of the source games — it proposes **no pycats camera design**
> (that is #803 → a downstream `decision:` with the human).

## TL;DR

1. **All three games run the same *family* of camera: an automatic bounding-box framer.** Each
   builds a box around all fighters, fits the view to it, and **hard-caps the zoom-out so the
   blast lines are never on-screen** — "The game's camera refuses to pan or zoom enough during
   gameplay to … 'see' the blast lines" (SmashWiki, *Blast line*, quoted for all three).
   The differences are in *parameters and feel*, not in the core algorithm.
2. **Melee is the only one we can read as code.** The `doldecomp/melee` decomp gives the exact
   algorithm: box = min/max sweep of "subjects", scaled by a per-fighter-count weight table
   `cm_803BCB9C = {0, 1.5, 1.32, 1.16, 1.0}` × `Stage_GetCamTrackRatio()`; camera distance fits
   the box to `tan(fov)` then clamps to `[Stage_GetCamZoomRate(), Stage_GetCamMaxDepth()]`;
   position/FOV/interest all **ease** toward target each frame (lerp factor clamped `[0.0001, 1.0]`).
   Every spatial/angular limit is per-stage (`Stage_GetCam*`).
3. **Brawl is the same shape but un-decompiled — only per-stage *box data* is quotable, no engine
   constants.** Stage `.pac` files store a camera box (`CamLimit0N`/`CamLimit1N`) and a larger
   death box (`Dead0N`/`Dead1N`) in the `stageposition` model. **No primary source gives Brawl's
   zoom-speed / smoothing / screen-shake numbers** — the "Brawl feels sluggish and more zoomed-in
   than Melee" consensus is qualitative community opinion, not a sourced constant.
4. **Project M RETUNES Brawl's camera; it does not replace the algorithm.** PM runs on Brawl's
   camera engine and edits per-stage data: BrawlBox exposes PM-named stage-parameter fields
   `CameraSpeed`, `CharacterBubbleBufferMultiplier`, `HorizontalRotationFactor`,
   `VerticalRotationFactor`, and PM's camera is copyable stage-to-stage as data — the signature of
   a data-retune. On top of that PM adds an **unrestricted free/snapshot camera** ("zooming out
   indefinitely and fully rotating") and (from 3.5) **respawn refocus**. Net player-facing feel:
   wider / more zoomed-out / more Melee-adjacent than Brawl.
5. **The off-screen "magnifying glass" bubble is the same mechanic in all three** and is
   **geometrically the ring between the camera box and the death box**: a fighter outside
   `CamLimit` but inside `Dead` is drawn in a hoop with a return arrow, taking **1%/sec, capped at
   150%** (SmashWiki). Brawl calls it "hoop damage"; Melee additionally renders a blocky low-res
   model. Ultimate's "Special Zoom" impact effect exists in **none** of the three.
6. **Sourcing asymmetry is the headline caveat for #803.** Melee camera *behaviour* is
   code-sourced; Brawl/PM camera *feel* (zoom speed, smoothing, shake) is **not sourced anywhere
   readable** — it lives in Brawl's un-decompiled engine, the same wall as the smash-charge-cap
   global (#637 / research epic #638). Any pycats "camera feel" number would therefore be a design
   **decision** or labelled inference, never a sourced PM value. The one thing that *is* sourced to
   the integer is the **per-stage box geometry** (pycats datamine #790).

---

## Q1 — Per-game camera behaviour

### Melee (code-verified from `doldecomp/melee`)

**Bounding region.** The camera enumerates fighters as "subjects", counts them, and sweeps a
min/max box. `CameraBounds` is `{ float x_min; float y_min; float x_max; float y_max; int
total_subjects; float z_pos; }` (`cm/types.h`, verbatim). The build loop (`camera.c`):

```c
for (subject = cm_804D6468; subject != 0L; subject = subject->prev) {
    if (Camera_8002928C(subject)) { subject_count++; }
}
...
min_x = min_y = F32_MAX;
max_x = max_y = -F32_MAX;
```

**Box scaling by fighter count.** The box is multiplied by a per-count weight table times a
per-stage ratio (`camera.c`, verbatim):

```c
static f32 cm_803BCB9C[5] = { 0.0f, 1.5f, 1.32f, 1.16f, 1.0f };
...
tracking_weight = cm_803BCB9C[subject_count];
tracking_multiplier = tracking_weight * Stage_GetCamTrackRatio();
```

⟨inference⟩ Indexed by active-subject count: 1 fighter → 1.5, 2 → 1.32, 3 → 1.16, 4 → 1.0 (index 0
unused). Read literally, **fewer fighters get more padding**, converging to 1.0 as the crowd grows.
Per-index semantics are a reading of the table + index, not an in-source comment.

**Zoom limits (fit-then-clamp).** Distance is computed to fit the box to the frustum, taking the
larger of the width- vs height-driven distance, then hard-clamped (`Camera_80029BC4`, verbatim):

```c
float cam_dist = (bounds->y_max - bounds->y_min) / tanf(MTXDegToRad(transform->target_fov));
float x_dist   = (bounds->x_max - bounds->x_min) /
                 (cm_803BCB64.aspect * tanf(MTXDegToRad(transform->target_fov)));
if (x_dist > cam_dist)                      { cam_dist = x_dist; }
if (cam_dist < Stage_GetCamZoomRate())      { cam_dist = Stage_GetCamZoomRate(); }   // zoom-IN floor
if (cam_dist > Stage_GetCamMaxDepth())      { cam_dist = Stage_GetCamMaxDepth(); }   // zoom-OUT ceiling
bounds->z_pos = cam_dist;
```

The **zoom-in floor** is `Stage_GetCamZoomRate()`; the **zoom-out ceiling** is
`Stage_GetCamMaxDepth()`. Both are **per-stage getters** — there is no single hardcoded zoom number
in the camera module.

**Smoothing (per-frame ease, not snap).** The interest point eases toward target each frame
(`Camera_80029AAC`, verbatim):

```c
offset_x = transform->target_interest.x - transform->interest.x;
...
lerp_factor = (follow_speed * speed) * delta;
if (lerp_factor > 1.0f)      { lerp_factor = 1.0f; }
else if (lerp_factor < 0.0001f) { lerp_factor = 0.0001f; }
transform->interest.x += offset_x * lerp_factor;
transform->interest.y += offset_y * lerp_factor;
```

FOV is eased the same way (`fov += delta * *fov_rate`). The smoothing rate is adaptive on box
"spread" (larger box → different follow speed) and the base constant is `Stage_GetCamTrackSmooth()`
— i.e. **per-stage tuned**. ⟨inference⟩ This is a per-frame exponential ease-out (spring-like), read
from the `+= delta * factor` shape and the `[0.0001, 1.0]` clamp — not a fixed-duration tween.

**Launched-fighter / blast-zone response.** A launched fighter widens the box, raising `cam_dist`,
but `cam_dist` is capped at `Stage_GetCamMaxDepth()`, so the camera **stops zooming out** and the
fighter passes the frame edge into the magnifying glass (Q3). Subject positions are also clamped
against `Stage_GetCamBounds{Left,Right,Top,Bottom}Offset()` before entering the box.

**Idle / one-player & manual camera.** With one subject the widest weight (1.5) keeps a lone
fighter loosely framed ⟨inference⟩. In single-player, a manual camera exists: "The control stick is
used to move the camera around and pressing the L or R buttons cycles through close-ups… it's also
possible to zoom manually by tilting the C-Stick" (SmashWiki, *Camera*).

### Brawl (data-verified + qualitative — engine un-decompiled)

**Automatic fit-to-players, with an excessive-zoom-out tail on big stages.** "During a match, the
camera zooms automatically to show all characters" and "on large stages such as Temple, 75m and New
Pork City, this can cause the camera to zoom out excessively" (SmashWiki, *Camera*, verbatim).

**Hard zoom-out ceiling relative to the kill boundary.** "The game's camera refuses to pan or zoom
enough during gameplay to … 'see' the blast lines" (SmashWiki, *Blast line*, verbatim) — same
never-see-the-blast-line property as Melee.

**Per-stage bounds live in the `.pac`, not in quotable engine code** (see Q2). The camera box is
`CamLimit0N`/`CamLimit1N`; the death box is `Dead0N`/`Dead1N`.

**Special-mode camera variants.** "Special Smash modes exist with slightly altered camera physics,
allowing the camera to be locked in place or tilted at an angle" (SmashWiki, *Camera*, verbatim).

**Feel vs Melee — qualitative only.** Community consensus holds Brawl's camera is more sluggish and
more zoomed-in than Melee's faster, tighter tracking. ⟨inference / community⟩ **No primary source
gives a numeric smoothing/lerp or zoom-speed constant for Brawl** — this is opinion, not a sourced
value. `brawllib_rs` / rukaidata do **not** parse stage camera bounds at all (their `Camera` struct
is a single-fighter move-preview framer), so the datamining path that reads fighter animations
cannot read the camera.

### Project M (retune of Brawl — same engine, edited data)

**Verdict: RETUNE, not replace.** Evidence that PM rides Brawl's camera engine and edits per-stage
data rather than swapping the algorithm:

- BrawlBox added **PM-named stage-parameter fields**: "Renamed STPM fields 15, 16, 17, and 19 to
  HorizontalRotationFactor, VerticalRotationFactor, CharacterBubbleBufferMultiplier, and
  CameraSpeed" (BrawlBox `Changelog.txt`, GitHub raw, verbatim). These are exactly the knobs a
  data-retune would tune.
- PM's camera is **portable as data** — community threads document copying PM's camera (the STPM +
  camera bones) into non-PM stages ("Installing 3.0 Camera on non-PM stages"; "How to give stages
  PM 3.5 camera and blast zones"). Copy-as-data is the signature of a parameter retune, not an
  engine rewrite. ⟨community, snippet-only⟩

**On top of the retune, PM adds an unrestricted free/snapshot camera.** "Altered camera that is
capable of zooming out indefinitely and fully rotating around the characters and stages, allowing
players to take snapshots without any camera restrictions" (SmashWiki, *Project M*, verbatim).
⟨inference⟩ This free-camera capability is most likely an engine/codeset addition rather than stage
data — but **no PMDT / codeset / `.gct` document was quotable** this pass, so the "free camera is
engine-level" claim is inference.

**Respawn refocus (3.5+).** "When a character is respawning, the camera refocuses instead of staying
focused on the characters that are currently still alive" ⟨wiki/community, needs-verification — this
sentence surfaced via search but was not reproduced in a direct page fetch⟩.

**Fixed-camera option is buggy.** A fixed-camera mode exists but is "completely dysfunctional on
numerous stages, often by being off-center" ⟨wiki, needs-verification — surfaced via search, likely
in a Glitches subsection⟩. ("Turbo" is a gameplay mode, not a camera setting — do not conflate.)

**Net feel.** Wider / more zoomed-out / more Melee-adjacent framing than vanilla Brawl. The
direction is sourced (the "zoom out indefinitely" quote + the Brawl auto-zoom baseline); the
*magnitude* is not — ⟨inference⟩ on where the retuned `CameraSpeed` / bubble-buffer land.

---

## Q2 — Cross-game diff (the deliverable)

### Behaviour comparison

| Behaviour | **Melee** | **Brawl** | **Project M 3.6** |
|---|---|---|---|
| Core algorithm | Auto bounding-box framer, **code-verified** (`camera.c`) | Auto bounding-box framer, engine un-decompiled | **Same engine as Brawl**, retuned |
| Box scaling | Per-count weight `{0,1.5,1.32,1.16,1.0}` × `Stage_GetCamTrackRatio()` (verbatim) | ⟨inference⟩ analogous auto-fit; no quotable constant | ⟨inference⟩ Brawl's, retuned via STPM |
| Zoom-in floor | `Stage_GetCamZoomRate()` (per-stage getter) | Governed by stage `CamLimit` box; ⟨no quotable number⟩ | Retuned per-stage (`CamLimit` + `CameraSpeed`) |
| Zoom-out ceiling | `Stage_GetCamMaxDepth()` (per-stage getter) | Stage `CamLimit`; "excessive" on big stages (verbatim) | Wider — "zoom out indefinitely" for free cam (verbatim) |
| Never sees blast line | Yes (verbatim, *Blast line*) | Yes (verbatim, *Blast line*) | Yes (inherits Brawl) |
| Smoothing | Per-frame ease, factor `[0.0001,1.0]`, rate `Stage_GetCamTrackSmooth()` (verbatim) | ⟨community⟩ "sluggish"; **no primary number** | ⟨community⟩ snappier/wider; **no primary number** |
| Stage-bounds mechanism | `Stage_GetCam*` getters → per-stage data (verbatim names) | `stageposition` bones in `.pac`: `CamLimit0N/1N`, `Dead0N/1N`, `CamCntrN` | Same bones, **retuned values** (datamine #790) + STPM fields |
| Off-screen bubble | Magnifying glass + blocky low-res model (verbatim) | "Hoop damage" hoop + arrow (verbatim) | Brawl's, `CharacterBubbleBufferMultiplier` tunes the buffer ⟨inference⟩ |
| Free / manual camera | Single-player C-stick/L-R only (verbatim) | Special-Smash lock/tilt only (verbatim) | **Unrestricted free + snapshot + full rotation** (verbatim) |
| Respawn framing | ⟨not separately sourced⟩ | Stays on living fighters ⟨inference⟩ | **Refocuses on respawn (3.5+)** ⟨needs-verification⟩ |
| Screen KO / crash-into-camera | Yes (`CameraQuake` shake bank, verbatim) | Yes — "crashes into the screen" + yell (verbatim, *Screen KO*) | Inherits Brawl |
| Ultimate-style "Special Zoom" | **No** (Ultimate-only, verbatim) | **No** (verbatim) | **No** |

### Numeric anchor — per-stage box geometry (the one thing sourced to the integer)

The camera box (`CamLimit`) and death box (`Dead`) are two opposite-corner boxes in the stage
`.pac`; `*0N` = top-left (min x, max y), `*1N` = bottom-right (max x, min y). Values below are
**pycats' own datamine** (#790, `docs/research/2026-07-31-pm-fd-blast-zone-floats.md`,
`scripts/datamine_stage_bounds.py`) plus a community debug-mode dump that agrees to the integer:

| Stage / bone | **Melee** (libmelee) | **Brawl base** (`STGFINAL`) | **PM 3.6** (`STGDXFINAL`) |
|---|---|---|---|
| FD `Dead` (L,R,T,B) | `(-246, 246, 188, -140)` | `(-240, 240, 180, -115)` | `(-246, 246, 188, -140)` |
| FD `CamLimit` (L,R,T,B) | n/a (Melee stores differently) | `(-180, 180, 130, -60)` | `(-170, 170, 114, -80)` |

**Key diff, sourced:** PM 3.6 FD's death box **exactly equals Melee FD's blast quadruple**
(`(-246,246,188,-140)`, corroborated by two independent datamines — libmelee's Melee table and
pycats' PM stage-bone read), while **Brawl base FD is slightly tighter** (`(-240,240,180,-115)`) —
so **PM widened the box and dropped the floor deeper toward Melee** (#790, verbatim). The community
"debug mode" dump (Smashboards, *Stage blast zones via debug mode*) reports FD `Dead0N (-246,188) /
Dead1N (246,-140)` and `CamLimit0N (-170,114) / CamLimit1N (170,-80)` — those are **PM's** numbers
(the dump was taken in PM), matching pycats' PM datamine exactly.

⟨no quotable number⟩ for any camera **feel** parameter (zoom speed, smoothing constant, screen-shake
magnitude) in Brawl or PM — see Q4.

---

## Q3 — Off-screen player handling (magnifying glass / "hoop damage")

Same mechanic across all three; the differences are naming and Melee's render.

- **Where it appears (threshold).** "When a fighter is off-screen but not past the blast line, they
  are still shown inside a small hoop known as the magnifying glass at the edge of the camera
  boundary" (SmashWiki, *Magnifying-Glass Damage*, verbatim). Geometrically it is **the ring between
  the `CamLimit` camera box and the `Dead` blast box** — the Smashboards debug dump labels the inner
  green square as "where your character appears as the magnifying glass icon" and the outer yellow
  square as the "… blast zone", and the `Dead` box is strictly larger than the `CamLimit` box.
- **What it renders.** A hoop "accompanied by an arrow that signals the player to get back
  on-screen" (verbatim). **Melee-specific:** "fighters in the magnifying glass have a blockier,
  lower-resolution model… These models cannot properly emulate some animations, such as blinking"
  (verbatim). Brawl names the effect **"hoop damage"** (the official Brawl site is quoted: "you
  incur a little bit of damage known as hoop damage").
- **Damage.** "at a rate of 1% per second, but stops occurring when the fighter has accumulated
  150% damage"; "does not occur in Training Mode nor in the All-Star Rest Area in Melee and Brawl"
  (verbatim). PM tunes the *framing buffer* via `CharacterBubbleBufferMultiplier` ⟨inference⟩; no
  sourced PM-vs-Brawl numeric delta for it.
- **Relation to KO.** The bubble occupies the gap between where the camera stops framing
  (`CamLimit`) and the KO boundary (`Dead`); crossing `Dead` is the KO. In pycats terms:
  `Fighter._outside_blast_zone` maps to the **`Dead`** box, and there is **no pycats analogue for
  `CamLimit`** because pycats has a fixed, non-scrolling camera (#790, verbatim).

---

## Q4 — Source quality & the decomp wall (why "feel" is unsourceable)

**The three games sit at three different sourcing tiers, and #803 must plan around that:**

- **Melee — code-verified.** The `doldecomp/melee` decompilation gives the algorithm and its
  constants byte-for-byte (`camera.c`, `types.h`). Everything in the Melee column above is read from
  source; only per-index *semantics* of the weight table and the ease *shape* are flagged
  ⟨inference⟩.
- **Brawl — data-verified, engine-opaque.** Brawl was never decompiled, so there is **no camera
  code to read**. What *is* primary is the per-stage box **data** in the `.pac` (`CamLimit*`,
  `Dead*`), readable via BrawlBox/BrawlCrate and pycats' `datamine_stage_bounds.py`. The camera's
  *behaviour* (zoom speed, smoothing, shake) is documented only qualitatively (SmashWiki) or as
  community opinion.
- **Project M — data-verified retune, engine-opaque + partly archive-locked.** PM's edits are
  visible as **data** (STPM fields, retuned bones) and confirmed by pycats' PM datamine. PM's own
  changelogs (3.0/3.02/3.5/3.6) that would date each camera change live in SmashBoards threads and
  the Wayback Machine, both of which blocked automated fetch this pass — so several PM claims are
  ⟨needs-verification / snippet-only⟩.

**The unsourceable gap (the finding #803 most needs).** There is **no primary source, for Brawl or
PM, giving a camera smoothing/lerp constant, a zoom-speed value, or a screen-shake magnitude.** That
number lives inside Brawl's un-decompiled engine — the **same engine-hardcoded-global wall** already
documented for the smash-charge-cap (#637) and mapped by research epic #638 (the only primary path
being a self-dumped RAM/DOL read). Consequences for pycats:

- A pycats camera can source its **box geometry** (blast/camera-box proportions) to the integer
  (#790) — that is solid ground.
- A pycats camera **cannot** source its *feel* (how fast it pans, how it eases, how hard it shakes)
  to any PM/Brawl primary. Those are either **Melee-analogous** (borrow the decomp's ease-toward-
  target shape and per-stage clamp structure, labelled "Melee-derived, PM feel unverified") or a
  **game-designer decision** (per RULES → "Changing values": bare game-feel without a citation is
  declined). #803 should treat camera feel as a `decision:`, not a value to be "found".

---

## Downstream & cross-refs

- **#803** — build-scoping spike (PM/Brawl auto-pan/zoom camera, "what must happen to build it").
  **Consumes this doc** for source-game behaviour. This doc's Q4 is the key input: box geometry is
  sourceable, camera feel is a decision.
- **#790 / #789** — PM FD blast-zone floats (datamined) + the blast-zone value decision (owner ruled
  "PM-faithful/scaled"). This doc reuses #790's numbers; it does not re-derive them.
- **#45** — `docs/research/screen-camera-sizing-findings.md`: pycats has no camera today; blast
  zones are `screen ± BLAST_PADDING`, hard-coupled to the 960×540 screen. A camera is a
  presentation-only viewport layer, golden-affecting.
- **#80** world-unit rendering · **#734** off-screen damage · **#638/#637** the engine-global decomp
  wall this doc's Q4 invokes.

## Out of scope (per ticket)

- Designing/scoping pycats's camera implementation — **#803**.
- The pycats render→screen pipeline (#803 Q2) and the world-coord KO decouple (#803 Q3 / #789).
- Larger-than-screen stage layouts (#661) and blast-zone value tuning (#789).

## Open gaps a follow-up could close (flag only — not filed)

1. Un-blocked SmashBoards / Wayback read of PM 3.0/3.02/3.5/3.6 changelogs → verbatim per-version
   camera lines (respawn-refocus, fixed-camera bug) and any PM-vs-Brawl STPM numeric deltas.
2. Confirm whether PM's free/snapshot camera is an engine/codeset change vs stage data (PMDT / `.gct`
   read).
3. OpenSA (dantarion) STDT/STPM field list — offline this pass — for the verbatim stage-parameter
   table semantics.
4. Any Brawl/PM camera *feel* number (smoothing, zoom speed, shake) would require Dolphin RAM / DOL
   inspection — the #638 route — not existing wiki text.
