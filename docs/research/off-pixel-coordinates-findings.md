# Decoupling the sim from pixel coordinates — research findings (#80)

> Can/should pycats move off raw pixel coordinates so it isn't defined in screen
> pixels? Follow-up to #45 (mapped the render path) and the shipped display arc
> (#82/#85/#92/#95 — resolution-independence *at render*). Read-only research →
> this doc + a recommendation. Confidence: high — audited directly at the code;
> not run through the deep-research harness. Date: 2026-06-25. Code @ 01ac2d8.

## TL;DR

- **"Run at any resolution" is already solved** (fixed 960×540 sim + scale-to-fit,
  #82/#85). This ticket is about the *deeper* question: defining the **sim** in
  abstract world units instead of pixels.
- **The sim is a hybrid:** float **velocity** (`pygame.Vector2`), but integer
  **position** (`pygame.Rect`). Every frame `rect.x += vel.x` **truncates** the
  float into an integer pixel (`core/physics.py:31-34`). That per-frame
  quantization is a **determinism asset** — it erases sub-pixel float divergence,
  so replay/parity don't depend on bit-identical floats.
- **Recommendation: do NOT move to abstract world units.** For a fixed-resolution
  fighter it's high-cost (retune every hitbox + knockback, regenerate every
  golden, take on cross-platform float-determinism risk, *lose* the int
  quantizer) for ~zero benefit over what scale-to-fit already delivers.
- **The one decoupling worth doing — and only when bigger stages / a camera (#45)
  are actually on the roadmap — is narrow:** introduce explicit **stage bounds**
  (`STAGE_WIDTH/HEIGHT`, defaulting to `SCREEN_WIDTH/HEIGHT`) and point the blast
  zones + platform layout + spawn positions at them. As an *identity refactor*
  (stage == screen) it's behaviour-preserving and **goldens stay green**. #45
  already deferred bigger stages, so there's no need to file it yet.

## Q — Does pygame-ce support non-pixel coordinates out of the box?

No (reaffirming #45/the prior #80 framing). The classic Surface API blits at
integer pixels; `FRect` stores floats but still snaps when drawn. The `_sdl2`
Renderer offers *resolution independence* (logical size + scale) but is still a
pixel rasterizer. A true **world-unit coordinate system is a pattern you build**
(keep the sim in floats/world units; convert world→pixels at the render boundary),
not a library feature.

## How pixel-bound is the sim today? (audit)

### Position & velocity — the crux
- `fighter.py:64-66`: `self.rect = pygame.Rect(...)` (integer position) + `self.vel
  = pygame.Vector2(0,0)` (float velocity).
- `core/physics.py:31-34` `move_rect`: `rect.x += vel.x` — float added to an
  **integer** `Rect.x`, so position **truncates to whole pixels every frame**. The
  fractional part is *not* carried in position; momentum persists only in `vel`.
- Consequence: position is always an integer; a sub-1px/frame velocity produces
  **no** movement. The sim's *observable state* is integer pixels.

### Everything else is pixels at the 960×540 scale
- **Physics constants** (`config.py`): `GRAVITY 0.5`, `MAX_FALL_SPEED 13`,
  `MOVE_SPEED 6`, `JUMP_VEL -13`, `DODGE_SPEED 14` — all px/frame.
- **Knockback** (`config.py:62-70`, `combat/knockback.py`, `fighter.py:173-175`):
  magnitude × `KNOCKBACK_LAUNCH_FACTOR 0.085` → px/frame; `KNOCKBACK_DECAY 0.145`
  px/frame. Comment: *"scaled to pycats' 960px stage."*
- **Blast zones / KO** (`fighter.py:183-189`): `rect.left > SCREEN_WIDTH +
  BLAST_PADDING` etc. — KO geometry is **`SCREEN_WIDTH/HEIGHT ± 50px`**, i.e.
  hard-coupled to screen size (no independent stage bound).
- **Platform layout & spawns** (`config.py:74-111`): every platform dim/offset and
  `PLAYERn_START_X/Y` is computed from `SCREEN_WIDTH/HEIGHT`.
- **Hitboxes** (`combat/data.py` `Circle`, `characters/default_cat.py`): circle
  `dx/dy/r` in **pixels**, hand-tuned for the 40×60 body ("reaches ~18px past the
  40-wide body").
- **Magic numbers**: edge-dodge `min_overlap = 25` (`fighter_physics.py`); jostle
  `overlap // 2 + 1` integer rounding (`core/physics.py:167-170`); all tail consts.
- **Headless runner** (`sim/runner.py`): no literal 960×540, but builds the stage
  from the `SCREEN_*`-derived config — *indirectly* coupled.

### Golden oracle — pixel-frozen
- `sim/runner.py` snapshots `p.rect.x, p.rect.y, round(p.vel.x,6), …` and
  `golden_util.serialize` JSON-encodes exact values. **Goldens freeze pixel
  coordinates**, so *any* change to sim coordinates (even a uniform rescale) breaks
  every golden until regenerated + reviewed.

## Q — Determinism & golden implications (the deciding factor)

- **Today's determinism is robust *because* position is integer.** The only floats
  are velocity ops; the per-frame `rect.x += vel.x` truncation **quantizes away**
  any sub-pixel float drift, so replay and the legacy≡statechart parity oracle
  don't hinge on bit-identical floating point across platforms.
- **Moving positions to float world units would remove that quantizer**, making
  replay/parity depend on reproducible float math everywhere — a real cross-
  platform determinism risk for a project whose core safety net is byte-identical
  goldens + parity.
- **Any sim-coordinate change invalidates all goldens.** The *only* way to change
  coordinates without a mass regen is an **identity transform** (new representation
  that computes the same integer pixels) — see the stage-bounds path below.

## Q — Is an `_sdl2` Renderer migration warranted? No.

Resolution independence at render is already shipped via the software
`scale_surface` path (#82/#85). `_sdl2` is a GPU/perf option, orthogonal to the
coordinate-unit question, and not needed here. Defer indefinitely.

## Q — Target coordinate model & recommendation

**Recommended: keep the sim in integer pixels at a fixed 960×540 internal
resolution.** It is simple, deterministic, well-tested, and already
resolution-independent at render. The hybrid float-vel / int-pos design is a
feature, not debt.

**Not recommended: an abstract world-unit coordinate system / float positions.**
Costs — retune every hitbox circle and the knockback launch/decay (empirically
fit to 960px), regenerate + hand-review every golden, take on float-determinism
risk, and *lose* the int quantizer — with **no benefit** over scale-to-fit for a
single fixed-resolution fighter. (If pixel-art crispness or huge stages were
core goals it might pay off; neither is.)

**The genuinely useful, narrowly-scoped decoupling** (separate from "world units")
is to break the **stage ≠ screen** coupling so a stage can differ from the window
and a camera (#45) becomes possible:
- Introduce `STAGE_WIDTH/HEIGHT` (default `= SCREEN_WIDTH/HEIGHT`) and a stage
  origin; point `_outside_blast_zone`, platform layout, and spawns at stage
  bounds instead of `SCREEN_*`.
- A camera/viewport then maps stage→screen at render (the identity-camera from
  #45's findings).

## Q — Incremental, behaviour-preserving migration path

1. **(Only when bigger stages / camera #45 are actually wanted) Stage-bounds
   identity refactor.** Replace `SCREEN_*` in blast/platform/spawn logic with
   `STAGE_*` defined equal to the screen. Pure rename/redirect → **same integer
   outputs → goldens stay green** (revert-check: diff snapshots before/after = 0).
   Sim-side, testable in isolation. This is the prerequisite #45 already named.
2. **(Separately, presentation only) Camera/viewport layer**, default identity —
   per #45, with its own golden baselines.
3. **World-unit coordinate system — not planned.** Recorded here as explicitly
   *not recommended*; revisit only if a future goal (pixel-art assets, continuous
   zoom sim, very large stages) changes the cost/benefit.

## Downstream

No ticket filed now — **per #45 bigger stages/camera are deferred**, so the
stage-bounds refactor (step 1) has no current need, and step 3 is not recommended.
If/when a camera or larger stage is scheduled, file the **stage-bounds identity
refactor** as the first slice (sim-side, golden-safe) and a camera ticket after.
The "move the sim to world units" idea should be considered **closed/not-pursued**
unless a goal change reopens it.

Refs: #45 (render path, camera deferral), #82/#85/#92/#95 (resolution-independence
at render, shipped), #38/#51 (combat tuning fit to the 960px stage).
