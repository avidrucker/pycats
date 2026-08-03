# Move-speed left/right symmetry — findings (#949)

**Role:** RESEARCH (repro/spec-first). Reproduces, quantifies, and root-causes the owner-reported
"Gnok appears to walk faster to the left than to the right." No code change in this ticket — the fix
is a separate DEV/decision ticket downstream (RULES → *research never produces the spec*).

**Date:** 2026-07-31 · **Agent:** DRAGONFRUIT · **Branch:** `br-dragonfruit/pycats-949-…`

---

## Verdict

**CONFIRMED — the asymmetry is real, deterministic, and sim-level (not a render artifact).**

- **Manifestation:** Gnok-specific *today*.
- **Root cause:** **global** — `pycats/core/physics.py::move_rect` truncates a fractional float
  velocity into pygame's integer `Rect` toward zero, so at a positive world-x a leftward step is
  `ceil(|vel.x|)` px while a rightward step is `floor(|vel.x|)` px. It only *shows* on Gnok because
  Gnok is the only cat with **fractional** ground speeds.

Leftward is the *faster* direction across the entire play region (all on-stage x is positive; see
"On-stage coordinate range" below).

---

## Measurements (headless sim)

Method: drive the real per-character speed values (`load_fighter_data(<cat>)`) through the real
integrator `pycats/core/physics.py::move_rect` for 14 frames from a positive on-stage x (480),
holding a constant leftward then rightward `vel.x = ±speed`. `step_horizontal` sets `vel.x` to
exactly `±speed` each frame (walk overrides friction), so steady-state velocity is the speed value;
the truncation happens in `move_rect`. Per-frame displacement is constant while x stays positive.

| cat | regime | speed (px/f) | left px/f | right px/f | delta (left vs right) |
|-----|--------|-------------:|----------:|-----------:|----------------------:|
| **gnok** | **walk** | **6.48** | **7** | **6** | **+16.7 % left** |
| **gnok** | **dash** | **9.72** | **10** | **9** | **+11.1 % left** |
| gnok | run | 8.00 | 8 | 8 | symmetric |
| nalio | walk / dash / run | 6 / 8 / 8 | =right | = | symmetric |
| narz | walk / dash / run | 6 / 8 / 8 | =right | = | symmetric |
| birky | walk / dash / run | 5 / 8 / 8 | =right | = | symmetric |
| testcat (default) | walk / dash / run | 6 / 8 / 8 | =right | = | symmetric |

Only Gnok's **walk (6.48)** and **dash (9.72)** are fractional, so only they are asymmetric. Gnok's
**run** defaults to `DASH_SPEED = 8` (integer) and is symmetric — Gnok never set a `run_speed`.

General law for a fractional speed `s` at positive x: `left = ceil(s)`, `right = floor(s)` px/frame,
so the bias is `1 / floor(s)` — **larger at slower speeds** (16.7 % at walk vs 11.1 % at dash).

---

## Root cause

`pycats/core/physics.py::move_rect`:

```python
def move_rect(rect: pg.Rect, vel: pg.Vector2) -> None:
    rect.x += vel.x   # pygame Rect coords are integers → the float is truncated toward zero
    rect.y += vel.y
```

pygame-ce 2.5.7 assigns a float to a `Rect` coordinate by **truncating toward zero**, verified
directly (`Rect.x = 100; x += 5.94 → 105` i.e. `round()` is *not* used, since `round(105.94)=106`).
Because the sim is fixed-timestep **integer-pixel** (#80), `rect.x` is an integer every frame, so the
fractional part of the velocity is discarded each frame — but the discard is **direction-asymmetric
at positive x**:

- moving **right** from integer `x`: `trunc(x + 6.48) = x + 6` → step `+floor(6.48) = 6` (undershoots by 0.48);
- moving **left** from integer `x`: `trunc(x − 6.48) = trunc(x − 6 − 0.48)`; since `x − 6.48` is still
  positive, truncation-toward-zero drops it to `x − 7` → step `−ceil(6.48) = −7` (overshoots by 0.52).

So a fractional speed travels `floor(s)` right but `ceil(s)` left — a fixed **1 px/frame** leftward bias.

### Where it is *not*
- **Not the tuning values.** `MOVE_SPEED`/`DASH_SPEED`/`DASH_DURATION`/`DOUBLE_TAP_WINDOW`
  (`pycats/config/physics.py`) and Gnok's `vel(1.2)=6.48` / `vel(1.8)=9.72`
  (`pycats/characters/gnok_cat.py`) are internally consistent; they merely *expose* the integrator bug
  by being fractional.
- **Not `step_horizontal`** (`pycats/systems/movement.py`): it sets `vel.x = ±move_speed`
  symmetrically (`+10 / −10` in its own unit test).
- **Not the input/facing path** (`pycats/entities/fighter_input.py`): `direction = 1 if right else -1`
  is a clean sign flip; facing does not scale speed.
- **Not friction** (`apply_horizontal_friction`): a held walk/dash overrides it to the flat speed each frame.

### Determinism (Q4)
This is a **deterministic sim** effect, reproducible headlessly with no render or display in the loop —
the sim positions genuinely differ frame-to-frame. It is **not** a render-only artifact.

### On-stage coordinate range (direction check)
`SCREEN_WIDTH = 960`; the FD floor (`STARTING_POINT`) spans x ≈ 18…942 and the thick platform x ≈
80…880 (`pycats/config/stage.py`); the left blast zone sits at x ≈ −50 (`BLAST_PADDING = 50`). So the
entire normal play region is **positive x**, where left is consistently the faster direction. Only in
the thin x ∈ [−50, 0] sliver just past the left blast zone (reached only while being KO'd) does
truncation-toward-zero invert the bias — irrelevant to live movement feel.

### Broader reach (context, out of scope to measure here)
`move_rect` integrates **every** float velocity — knockback slides, air drift, the dash burst — so the
same truncation biases any fractional `vel.x` leftward, not just ground walk/dash. This ticket's
verdict is scoped to ground walk/dash/run per its "Out of scope"; the wider reach is flagged for the
fix ticket to weigh.

---

## Option space for a fix (research reports options only)

A follow-on DEV/decision ticket owns the choice; the fix is **not** made here.

1. **Sub-pixel position accumulator (most faithful).** Carry a float x on the fighter, integrate in
   float, and derive the integer `rect.x` with a *symmetric* round (`round`/`floor`) only for
   collision/render. Keeps the fixed-timestep determinism (#80) while removing the per-frame
   truncation bias entirely, at any speed. Largest change — touches the entity/physics seam and the
   `pg.Rect`-is-the-position assumption; needs a golden re-bless if any shipped (integer-speed) cat's
   pixels shift (they should not, since integer speeds already land on integers).
2. **Symmetric quantization in `move_rect`.** Round `vel.x` to the nearest int *before* adding, so both
   directions take the same integer step (`round(6.48)=6` both ways). Cheap and localized, but
   **quantizes** the speed to an integer — abandons the sub-pixel intent of the `vel()` value (6.48
   would play as 6, 9.72 as 10).
3. **Author integer ground speeds.** Re-pin Gnok's walk/dash to integers (e.g. 6 and 10). Cheapest and
   restores symmetry, but discards the raw-first `vel()` faithfulness for ground speed and is really a
   tuning decision (needs a basis per RULES → *changing values*), not a bug fix.
4. **Accept + document.** Only viable if the bias were negligible — 16.7 % at walk is not; not recommended.

**Opinion (the commit gate is the human's, #865):** Option 1 is the correct long-term fix — it makes
*every* fractional velocity (knockback, drift, future `vel()`-authored cats) symmetric and preserves
the raw-first authoring intent, whereas Options 2–3 only paper over Gnok's two current values and will
recur the next time a fractional speed is authored. Option 1 is the larger change; if a fast interim
un-block is wanted, Option 3 (integer re-pin of Gnok walk/dash, with a tuning basis) removes the
visible symptom without touching the integrator.

---

## Downstream fix ticket
- **#979** (DEV, bug · area:combat/combat:physics) — implement the fix. The red-green non-vacuous
  reproduction (`tests/test_move_rect_symmetry.py`, parametrized over every character × walk/dash/run ×
  {equal L/R velocity, equal frames to travel 200px}) was transferred to #979's branch; currently
  26 pass / 4 fail, every failure Gnok walk/dash. Design note carried on #979: a naive per-frame
  `round(vel)` breaks gravity (`round(0.5)==0`), so the fix must round the **position** at the pygame
  boundary with a sub-pixel accumulator, not round the per-frame velocity. Owner has a plan for the approach.
