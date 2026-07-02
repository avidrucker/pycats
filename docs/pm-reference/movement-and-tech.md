# Movement & tech — PM mechanics reference

> How a fighter walks, dashes, jumps, falls, and drifts — and the **PM signature
> movement tech** (wavedash, L-cancel, dash-dance) that defines the mod's feel.
> This doc owns the movement *model*; the per-archetype attribute *values* live in
> [character-data-and-archetypes](./00-overview.md), the *state* names in
> [fighter-states](./fighter-states.md). Part of the
> [PM mechanics reference](./00-overview.md) ([epic #147](https://github.com/avidrucker/pycats/issues/147));
> PM 3.6, Brawl/Melee deltas noted.

**Audience:** a contributor — human or agent — about to implement or modify
movement / movement tech. Reference depth, not a tutorial; assumes the
[00-overview](./00-overview.md) conventions (60 Hz integer frames; speeds in PM
units/frame, **× `PX_PER_UNIT ≈ 5.4`** for pixels).

PM is built on Brawl but **restores Melee-style movement** — faster falling, more
air control, and the tech (wavedash, L-cancel, dash-dance) that base Brawl lacks.
That movement identity is the bulk of what makes a cat "play like" its archetype.

## Ground movement

- **Walk** — analog-speed stroll (tilt the stick); fully actionable.
- **Initial dash** — a tap gives a burst of speed; during the initial-dash window
  you can **dash-dance** (rapidly reverse) or **foxtrot** (re-dash).
- **Run** — holding the dash direction past the initial window; you can't freely
  turn (must skid/turnaround first).
- **Pivot** — a frame-perfect turnaround at the end of a dash, used to attack the
  other way with run momentum.
- **Skid / turnaround** — deceleration when reversing from run.

Worked example — **PM Mario** (units/frame): walk **1.1**, dash **1.5 / 1.55**.

## Jumps

- **Jumpsquat** — a few grounded startup frames before leaving the ground; you can
  **jump-cancel** (JC) certain actions (grab, up-smash, up-B) out of it.
- **Short hop vs full hop** — a *quick* jump press = short hop (lower); a held
  press = full hop. Distinct heights → different aerial timings.
- **Double jump** — one mid-air jump (more for floaty multi-jump characters).
- **Double-jump cancel (DJC)** — for characters that have it, an aerial cancels the
  double jump's rise, dropping them — a movement/spacing tool.

## Air movement

- **Air speed / drift** — horizontal control while airborne (lower than ground
  speed); lets you influence trajectory after a jump or launch.
- **Gravity & fall speed** — gravity accelerates the fall to a terminal fall speed;
  **fast-fall** (tap down past the jump apex) snaps to a faster terminal speed for
  the rest of the descent.
- **Momentum** — horizontal velocity **carries** between ground and air (a running
  jump keeps run speed); this is why DI and drift matter.

Worked example — **PM Mario**: air speed **0.86** u/f, gravity **0.095** u/f²,
fall speed **1.7** base / **2.3** fast-fall.

## PM signature tech

- **Wavedash** — **air-dodge diagonally into the ground** just after a jump: the
  air-dodge's momentum is preserved as a ground slide, giving an instant spaced
  reposition. (Mechanically it's the air dodge from
  [defense-shield-dodge](./defense-shield-dodge.md) angled into the floor; PM tunes
  air dodge to enable it.)
- **L-cancel** — pressing L/R (shield) just before landing during an aerial
  **halves the landing lag**, so aerials are far safer on shield and combo better.
- **Dash-dance / pivot / JC** — the Melee-derived ground tech above; PM restores
  them where Brawl removed or weakened them.

These are the **competitive-defining** mechanics PM adds on top of Brawl.

## Brawl / Melee / PM deltas

- **Tech restored:** wavedash, L-cancel, dash-dance, and strong pivots are
  Melee-isms **absent/weakened in base Brawl** and **restored by PM**.
- **Faster falling / less floaty:** PM raises gravity/fall speeds toward Melee
  feel vs Brawl's floatiness.
- **Air dodge:** Brawl = one omnidirectional dodge → helpless (no wavedash);
  Melee/PM = directional with momentum → wavedash. See
  [defense-shield-dodge](./defense-shield-dodge.md).
- **Unit note:** all speeds are PM units/frame; multiply by ≈ 5.4 for pixels
  ([00-overview](./00-overview.md) / [#120](https://github.com/avidrucker/pycats/issues/120)).

## Sources

- [`docs/research-120-smash-units-and-sources.md`](../research-120-smash-units-and-sources.md) — PM Mario walk/dash/air/gravity/fall/jump values and the `PX_PER_UNIT ≈ 5.4` derivation.
- [`docs/research/pm-mechanics-implementation-analysis.md`](../research/pm-mechanics-implementation-analysis.md) — Phase 5 (movement tech + PM signatures) roadmap.
- SmashWiki — [Wavedash](https://www.ssbwiki.com/Wavedash), [L-canceling](https://www.ssbwiki.com/L-canceling), [Dash-dance](https://www.ssbwiki.com/Dash-dance), [Fast-fall](https://www.ssbwiki.com/Fast-fall), [Jump](https://www.ssbwiki.com/Jump).
- State names: [fighter-states](./fighter-states.md); air-dodge numbers: [defense-shield-dodge](./defense-shield-dodge.md). Conventions: [00-overview](./00-overview.md).

## pycats status

Implemented:
- **Per-character movement constants** — `FighterData.gravity / max_fall_speed / move_speed / jump_vel / max_jumps`, read by the physics/input layer ([#126](https://github.com/avidrucker/pycats/issues/126)). Defaults (PM-Mario-calibrated): `GRAVITY = 0.5`, `MAX_FALL_SPEED = 13`, `MOVE_SPEED = 6`, `JUMP_VEL = -13`, `MAX_JUMPS = 2` (config). These land on `PX_PER_UNIT ≈ 5.3–5.6` vs the PM values above.
- **Horizontal movement** — `pycats/systems/movement.py::step_horizontal` (instant-ish, no analog walk ramp); **gravity + terminal fall** in `pycats/entities/fighter_physics.py`.
- **Jumps** — single + double via `max_jumps`/`jump_vel`; `run`/`jump`/`fall` states ([fighter-states](./fighter-states.md)).

**Deferred / not yet modelled:**
- **Walk vs dash vs run split** — only a single `run` exists (no analog walk, no initial-dash window).
- **Fast-fall** — `entities/player.py` carries a `#### TODO: implement fast fall`.
- **Short hop vs full hop**, **double-jump cancel**, **dash-dance / pivot / foxtrot** — none yet.
- **Wavedash & L-cancel** — gated on PM-deviation research ([#24](https://github.com/avidrucker/pycats/issues/24) thread c) and the Phase-5 roadmap; also depends on the air-dodge decisions ([#23](https://github.com/avidrucker/pycats/issues/23)/[#66](https://github.com/avidrucker/pycats/issues/66)).
- **Brawl vertical-KB gravity term** — pycats has one global gravity; not modelled.
- Divergences: [#99](https://github.com/avidrucker/pycats/issues/99). Open questions: [#24](https://github.com/avidrucker/pycats/issues/24). Roadmap: `docs/research/pm-mechanics-implementation-analysis.md` (Phase 5).
