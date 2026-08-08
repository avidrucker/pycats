# Findings: the launch physics pycats is missing (#43)

> Why authentic knockback *magnitudes* (#40) still launch fighters off-stage, and
> the authentic model that fixes it. Read-only research; feeds a Phase-1 child of #38.
>
> Evidence harness: `repros/probe_knockback_physics.py`. Sources: SmashWiki
> [Knockback](https://www.ssbwiki.com/Knockback), [Hitstun](https://www.ssbwiki.com/Hitstun).
> Date: 2026-06-24. Ticket #43; umbrella #38; surfaced verifying #40.

## 1. The symptom, measured

A single 0%→10% jab (KB = 56.4) sends the defender **503 px across the 960 px
stage**. The per-frame trace (probe script) shows why:

```
frame  vel.x    dx   hurt_t state
 1..21 22.56  22→462   21→1  hurt    # CONSTANT velocity for the whole hitstun
 22    22.56  484      0     idle     # hitstun ends
 23    11.28  495      0     run      # friction ONLY starts now
 ...    0.00  503      0     idle
```

The launch velocity is applied once and **never decays during hitstun** — pycats
skips `handle_move`/`step_horizontal` (where friction lives) while `in_hitstun`,
so the fighter slides ballistically at full speed for all 22 hitstun frames, then
friction abruptly engages. That is not how Smash works.

## 2. How Smash actually launches a fighter

Knockback magnitude (the `KB` we already compute in `pycats/combat/knockback.py`)
is **not** a velocity. It drives a small kinematic model (Melee/Brawl/PM share the
same internal units):

| Quantity | Formula | Constant | Confidence |
|---|---|---|---|
| Initial launch **speed** | `KB × 0.03` units/frame | **0.03** | SmashWiki Knockback, explicit |
| Per-frame **decay** | `speed -= 0.051` each frame until 0 | **0.051** | SmashWiki Knockback, explicit |
| **Hitstun** | `floor(KB × 0.4)` frames | **0.4** | SmashWiki Hitstun (Melee/Brawl). PM is Brawl-based and removed *hitstun cancelling*; multiplier unchanged. ⚠ confirm no PM tweak |

So the launched fighter **decelerates every frame from the moment of the hit** —
during hitstun and beyond — until momentum is gone. Travel distance is the
arithmetic-series sum, ≈ `launch_speed² / (2 × decay)`, i.e. **distance ∝ KB²**.

Worked (Smash units):
- KB 56.4 (10% jab): launch `1.69`/f, stops in `1.69/0.051 ≈ 33` f, travels `≈ 28` u.
- KB 132 (100%): launch `3.96`/f, stops in `≈ 78` f, travels `≈ 154` u.

Note the decoupling: at 56.4, hitstun is 22 f but the slide lasts ~33 f — the
fighter is **still drifting, now actionable** (can tech/DI) for ~11 f. pycats has
no such window; it stops dead the instant friction starts.

## 3. The gaps, ranked

1. **No knockback decay during hitstun — PRIMARY.** This is the whole symptom.
   pycats applies launch velocity once and lets it ride; Smash bleeds it off at a
   fixed rate from frame 1. Without decay, `distance = launch_vx × hitstun`, and
   since both scale with KB the travel explodes (∝ KB²) at the placeholder scale.
2. **KB→launch-speed conversion is a free knob, not the real constant.** `#40`'s
   `KNOCKBACK_VELOCITY_SCALE = 0.4` stands in for Smash's `0.03`. It must be
   replaced by the decay-model pair (below), not hand-tuned in isolation.
3. **Pure horizontal launch angle (0°).** The cat jab launches at angle 0, so
   there is no vertical component for gravity to arc down and no ground re-contact
   to add traction. Real grounded hits use the Sakurai angle (361) — a low arc —
   so the target skids and gravity/ground help stop it. (Deferred mechanic, but it
   compounds the slide.)
4. **All friction is skipped in hitstun.** Even ignoring a bespoke decay, a
   grounded launched fighter should feel **traction**. pycats applies *zero*
   horizontal deceleration during `hurt`/`stun`.
5. **Flat per-character stats.** `weight` (100), `GRAVITY` (0.5), `MAX_FALL_SPEED`
   (13), `GROUND_FRICTION`/`AIR_FRICTION` are global. Fidelity eventually needs
   per-character weight/gravity/fall-speed/traction; not the cause of *this* bug.
6. **Hitstun↔travel coupling / DI.** Once decay exists, hitstun and travel
   decouple and DI/SDI/hitstun-cancel-removal become meaningful (later phases).

## 4. Important nuance: lowering the scale alone is *not* the fix

Because the current model already gives `distance ∝ KB²` (velocity ∝ KB × hitstun
∝ KB), dropping `KNOCKBACK_VELOCITY_SCALE` to ≈ **0.06** would make the *magnitude*
roughly sane (10% jab ≈ 80 px, 100% ≈ 440 px). **But it leaves the motion wrong:**
a constant-velocity slide that stops dead when hitstun ends — robotic, no ease-out,
and travel rigidly equal to `velocity × hitstun`. The authentic decay model fixes
the *feel* and decouples the constants. **Recommendation: implement decay; treat a
scale drop only as an optional stopgap if a playable build is needed first.**

## 5. Recommended model for pycats (the implementation ticket)

Replace `KNOCKBACK_VELOCITY_SCALE` with the two-constant decay model, applied in
pixel space but preserving Smash's ratio (`decay/launch = 0.051/0.03 = 1.7`, so
frames-to-stop `= launch_speed/decay = KB/1.7 ≈ 0.59 × KB`, scale-independent):

```
launch_speed_px = KB * KNOCKBACK_LAUNCH_FACTOR        # initial px/frame
# each frame while a knockback is active (INCLUDING hitstun):
#   reduce the knockback component toward 0 by KNOCKBACK_DECAY
#   (gravity still acts on the vertical component)
```

Pick the pixel scale from a target feel on the 960 px stage. To land a 10% jab at
≈ 80 px (light tap) while preserving the 1.7 ratio:

| Constant | Value | Basis |
|---|---|---|
| `KNOCKBACK_LAUNCH_FACTOR` | **≈ 0.085** px/frame per KB unit | tuned so KB 56.4 → ~80 px travel |
| `KNOCKBACK_DECAY` | **≈ 0.145** px/frame per frame | `1.7 × LAUNCH_FACTOR` (Smash ratio) |

Resulting travel (`distance ≈ 0.0249 × KB²` px): 10% jab ≈ 80 px, 100% ≈ 435 px,
150% ≈ 755 px (a 150% hit from centre nearly reaches the blast zone — a launcher/KO,
as it should be) — a real "light jab vs launcher" curve, with continuous ease-out
and a short actionable drift tail.
All three are **playtest starting points**, flagged like the spec's other constants.

**Structural change:** in `Player.update`, while a knockback is active, decay the
horizontal knockback velocity by `KNOCKBACK_DECAY` toward 0 each frame instead of
skipping all horizontal physics. The cleanest separation is to track the knockback
contribution distinctly from input-driven velocity (so DI/input later compose),
but a first cut can simply decay `vel.x` during `hurt` and resume friction after.
Preserve #8 (momentum combine) and re-verify with `repros/probe_knockback_physics.py`
(travel should now ease out frame-by-frame, not hold constant).

## 6. Scope of the implementation child of #38

In: the decay model + the two constants + applying decay during hitstun; retire
`KNOCKBACK_VELOCITY_SCALE`; golden regen (semantic verify); probe re-run.
Out (separate slices): Sakurai/launch-angle realism, per-character stats, DI/SDI.

## Sources
- SmashWiki — Knockback: launch speed `= KB × 0.03`; decay `0.051`/frame.
  https://www.ssbwiki.com/Knockback
- SmashWiki — Hitstun: `floor(KB × 0.4)` (Melee/Brawl; PM Brawl-based, hitstun
  cancelling removed). https://www.ssbwiki.com/Hitstun
- Live evidence: `repros/probe_knockback_physics.py` (this repo, gitignored).
