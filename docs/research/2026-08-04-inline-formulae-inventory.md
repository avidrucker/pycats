# Inline-formulae inventory — unit/coord conversions + physics/game rules

**Ticket:** #1226 (RESEARCH) · **Follow-up:** #1227 (DEV, sequenced after this) ·
**Date:** 2026-08-04 · **Agent:** APPLE

## Question

Where in pycats does an **inline formula** live — arithmetic encoding either a
**unit/coordinate conversion** (unit→pixel, world→screen) or a **physics/game rule**
(gravity/fall, knockback, velocity, hitstun, DI, decay, timing) — instead of reading
through a **named function** for that rule?

Scope, per the ticket: (1) unit/coord conversions [ADR-0011 `units.u()`/`vel()` seam],
(2) physics/game-rule formulae. **Out of scope:** pure UI/layout math, colour/animation
interpolation, and magic-number expressions that are neither a conversion nor a game rule.

## Headline

**The seams are broadly healthy.** Both the conversion boundary and the core physics
formulae are already factored into named functions; the inline-formula surface is small.

- **Conversion family — zero offenders.** There is **no** inline `× PX_PER_UNIT` / `× 5.4`
  anywhere outside the seam itself (`pycats/combat/units.py::u`/`vel`). Every spatial
  unit→px site (jostle, stage bounds, dodge/air-dodge, hitbox data) already goes through
  `u()`/`vel()` or is a config-level `round(units * PX_PER_UNIT)` constant with its
  provenance row. The recurring ADR-0011 correction has effectively landed.
- **World→screen — no offenders.** The sim is integer-pixel (#80); render reads
  `p.rect.x/.y` directly, so there is no separate camera/world→screen transform to route.
  (`render/body.py`'s `* s` squash-stretch scaling is animation, out of scope.)
- **Physics rules — mostly factored.** Gravity/fall (`core/physics.py::apply_gravity`),
  friction + dead-zone (`apply_horizontal_friction`), the full Brawl/PM knockback equation
  (`combat/knockback.py::knockback`/`set_knockback`), hitstun (`hitstun_frames`), hitlag
  (`hitlag_frames`), decay (`decay_velocity`), Sakurai angle (`sakurai_angle`), shield-break
  stun (`shield.py::shield_break_stun_frames`), shieldstun (`shieldstun_frames`), and smash
  charge (`combat/charge.py::charge_multiplier`) are all named functions.

What remains is a short list of call-site arithmetic, enumerated below.

## Inventory

Landmark = `pkg/mod.py::Symbol`. "Seam?" = does a named home already exist. Verdict ∈
{clean-extract, needs-a-decision, leave-inline}.

### Conversion family

| # | Landmark | Expression | Seam? | Verdict |
|---|----------|-----------|-------|---------|
| C1 | `systems/status_model.py` (COUNTDOWN readouts) | frame→seconds computed **three ways**: `_secs(frames)` (=`math.ceil(frames/FPS)`), inline `math.ceil((SMASH_CHARGE_FRAMES-charge_timer)/FPS)`, and `math.ceil(shield_hp/(SHIELD_DRAIN_PER_FRAME*FPS))` | partial — `_secs()` exists but two sites bypass it | **needs-a-decision** — HUD readout (leans out-of-scope), but the seam exists and is applied inconsistently; DEV/human calls whether to route all three through `_secs`/a `frames_to_seconds` helper |

No other conversion-family sites. (`u()`/`vel()` seam adoption is complete for spatial math.)

### Physics-rule family

| # | Landmark | Expression | Seam? | Verdict |
|---|----------|-----------|-------|---------|
| P1 | `entities/fighter.py::Fighter.receive_hit` | `round(shield_hp - SHIELD_DRAIN_PER_FRAME, 2)` (drain) / `+ …` (regen) | no — belongs beside `shield_break_stun_frames`/`shieldstun_frames` in `combat/shield.py` | **clean-extract** — self-contained per-frame integration; the `config/physics.py` `SHIELD_DRAIN_PER_FRAME` comment still says "keep in sync with the literal in player.py's shield tick" (**stale** — the tick moved to `fighter.py` in the S3 consolidation, no player.py duplicate remains), which is exactly the drift hazard a named `shield_drain(hp)`/`shield_regen(hp)` removes |
| P2 | `entities/attack.py::Projectile.update` | `vy = -vy * self.restitution` (bounce reflection) | no — natural home `core/physics.py` | **clean-extract** — a named `bounce_velocity(vy, restitution)` reads as the rule; single self-contained expression |
| P3 | `entities/fighter.py::Fighter.receive_hit` | `launch = kb * KNOCKBACK_LAUNCH_FACTOR`; `vel.x += launch*cos(θ)*dir`; `vel.y = launch*-sin(θ)` | no | **needs-a-decision** — a `launch_velocity(kb, angle_deg, facing)` is tempting, but the `+=` on x vs `=` on y is a deliberate momentum-combine rule (#8: launch adds to horizontal momentum, overrides vertical arc). Any extraction must preserve that asymmetry — a semantic seam decision, not a mechanical lift |
| P4 | `entities/fighter.py::Fighter.receive_hit` | `kb *= CROUCH_CANCEL_FACTOR` | no | **needs-a-decision** — a one-line state-gated multiply; `crouch_cancel(kb)` may be over-extraction. DEV/human calls whether it earns a function |
| P5 | `entities/fighter_input.py` (charge tick) | `f.charge_fraction = f.charge_timer / SMASH_CHARGE_FRAMES` | `combat/charge.py` is the natural home (already holds `charge_multiplier`) | **needs-a-decision** — trivial ratio, but co-locating a `charge_fraction(timer)` next to `charge_multiplier` has mild pull; low value on its own |
| P6 | `entities/attack.py::Projectile.update` | `vy += self.gravity` (projectile gravity, **no** max-fall cap) | `apply_gravity` exists but caps at `MAX_FALL_SPEED` | **needs-a-decision** — projectiles are deliberately capless; routing through `apply_gravity` would wrongly impose the fighter fall cap. If extracted, needs a cap-less variant, not the existing seam |

## Summary counts

- **Conversion family:** 0 inline `× PX_PER_UNIT`/`× 5.4` offenders; 1 time-conversion
  inconsistency (C1, needs-a-decision).
- **Physics-rule family:** 6 inline sites — **2 clean-extract** (P1 shield drain/regen,
  P2 projectile bounce), **4 needs-a-decision** (P3 launch vector, P4 crouch-cancel,
  P5 charge fraction, P6 projectile gravity).
- **leave-inline:** none flagged — the low-value sites are folded into needs-a-decision so
  the DEV/human makes the "is it worth a function" call explicitly.

## Shortlist (highest-value conversions)

1. **P1 — shield drain/regen → `combat/shield.py`.** The only site with a live drift
   hazard: a stale "keep in sync" comment in `config/physics.py` points at a duplicate that
   no longer exists, and the rule sits away from its sibling shield formulae. Cleanest win.
2. **P2 — projectile bounce → `core/physics.py::bounce_velocity`.** A textbook
   self-contained physics rule; names cleanly, no seam ambiguity.
3. **P3 — launch-velocity vector.** Highest gameplay value but **not** a clean lift: the
   `+=`/`=` momentum asymmetry is the reason to bring a human into the DEV decision.

## Asides (not inline-formula offenders, but surfaced by the sweep)

- **`combat/charge.py::charge_multiplier` has zero call sites** — the smash-charge
  damage/knockback scaling is defined but not yet wired into `receive_hit`. Not a formula
  duplication (nothing inlines it), but an orphan named seam. Folded into the broader
  uncalled-functions sweep, **#1232** (as an orphan-by-design instance), outside this
  inventory's scope.
- **`config/physics.py` `SHIELD_DRAIN_PER_FRAME` comment is stale** (points at a removed
  player.py literal) — fix rides along with P1.

## Refs

ADR-0011 (unit→px `units.u()` seam) · `docs/mechanics-index.md` §B · `combat/provenance.py`
(constant registry) · #1227 (DEV follow-up — converts the P1/P2 clean-extract sites) ·
**#1233** (ARC — rules on the 5 needs-a-decision sites P3–P6/C1 before #1227 touches them) ·
**#1232** (RESEARCH — uncalled-functions sweep, home of the `charge_multiplier` orphan).
