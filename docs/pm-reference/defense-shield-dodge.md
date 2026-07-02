# Shield & dodges — PM mechanics reference

> The **defensive numbers**: how shielding absorbs a hit, how the shield breaks,
> and the dodge family. This doc owns the shield/dodge *values*; the *state*
> names it uses (Guard, shieldstun, dodge) are mapped in
> [fighter-states](./fighter-states.md). Part of the
> [PM mechanics reference](./00-overview.md) ([epic #147](https://github.com/avidrucker/pycats/issues/147));
> PM 3.6, Brawl/Melee deltas noted.

**Audience:** a contributor — human or agent — about to implement or modify
shielding/dodging. Reference depth, not a tutorial; assumes the
[00-overview](./00-overview.md) conventions (60 Hz integer frames).

## Shield

Holding shield raises a **bubble** that blocks hits at the cost of shield HP.

| Quantity | PM/Brawl value |
|---|---|
| Max HP | **50** (≈71.43 effective: incoming damage hits the shield at a 0.7× multiplier) |
| Depletion (held) | **0.28 / frame** (16.8/s) |
| Regen (not held) | **0.07 / frame** (4.2/s) |
| Full-HP hold time | ~2.98 s |

- **Sub-states:** GuardOn (startup) → Guard (holding) → GuardOff (release lag).
  You're committed through GuardOn/Off frames.
- **The bubble shrinks** as HP drops and grows around the body; its size + position
  drive **shield poke** (below).
- **Light shield** (variable density) is **Melee-only** — not in Brawl/PM.

### Shield poke — contact is geometry, not HP
Whether a hit is blocked is decided by **geometry, not remaining HP**:

> If an attacker's hitbox touches the shield bubble **at all** → blocked
> (defender takes shieldstun, shield loses HP). A **poke** (damage through the
> shield) happens only when the hitbox reaches an **exposed hurtbox without
> touching the bubble** — e.g. a low/disjointed hit slips under a shrunken shield.

So "enough HP left" doesn't decide blocking; HP only decides how small the bubble
has shrunk (and thus how much hurtbox pokes out). The shield always wins the
*contact* — this is the **shield-priority** rule.

### Shieldstun
A blocked hit locks the defender in shield (no OOS action) for:

```
shieldstun = floor(damage × 0.345)      (attacks < ~2.9% → 0 frames)
```

The attacker also takes shield **hitlag** (the freeze), and shieldstun runs
**after** hitlag — see [combat-knockback-hitstun](./combat-knockback-hitstun.md).

### Shield break → dizzy stun
If a hit drops shield HP to 0, the shield **breaks** and the fighter is launched
up then **dizzy-stunned** (helpless, all input locked) for a damage-scaled time —
uniquely **decreasing** with percent:

```
dizzy = (400 − p) + 90  frames,  clamped [90, 490]      (490 at 0%, 90 at ≥400%)
```

### Out-of-shield (OOS) options
From Guard you can act without a full GuardOff: **jump** (→ aerial / up-B / up-smash
out of jumpsquat), **grab** (the dedicated OOS grab), **spot dodge / roll**, or
**shield drop**. OOS speed is a core defensive metric.

## Powershield / parry

PM adds a **powershield/parry**: a tightly-timed shield press as the hit lands
**negates shieldstun (and reflects projectiles)**, giving a big frame advantage —
PM's risk/reward replacement for Melee's reflect-powershield. (PM-specific; only
lightly corroborated in datamined frame data — treat exact windows as approximate.)

## Dodges

All dodges grant **intangibility** for an active window inside a fixed total
duration (startup vulnerable → intangible → recovery vulnerable):

- **Spot dodge** — in place, grounded; dodge a hit without moving.
- **Roll** (forward / back) — travels a set distance grounded; turns you around;
  vulnerable on the startup/recovery edges (the punish window).
- **Air dodge** — a single airborne dodge with a directional boost; in Brawl it
  forces **helpless** (special-fall) afterward. PM reworks air dodge toward Melee
  feel (it feeds wavedash — see [movement-and-tech](./00-overview.md)), changing
  whether/when helpless follows.

Intangibility is the orthogonal tangibility flag from
[combat-hitboxes-priority](./combat-hitboxes-priority.md); overusing dodges is
punishable because the recovery frames are vulnerable.

## Brawl / Melee / PM deltas

- **Light shield** — Melee-only (density change); absent in Brawl/PM.
- **Powershield/parry** — PM-added; Melee's powershield reflected only; Brawl's
  was weaker. PM's parry (zero-shieldstun window) is a PM signature.
- **Air dodge** — Brawl = one omnidirectional dodge → helpless; Melee/PM = directional
  with momentum (wavedash). PM tunes this deliberately.
- **Shieldstun** — PM increased shieldstun vs Brawl for balance; the `×0.345`
  factor is the documented family figure.

## Sources

- [`docs/research/brawl-projectm-fighter-states.md`](../research/brawl-projectm-fighter-states.md) — shield HP/drain/regen, shieldstun, shield-priority geometry (deep-research, adversarially verified).
- SmashWiki — [Shield](https://www.ssbwiki.com/Shield), [Shield poke](https://www.ssbwiki.com/Shield_poke), [Shieldstun](https://www.ssbwiki.com/Shieldstun), [Powershield](https://www.ssbwiki.com/Powershield), [Dodge](https://www.ssbwiki.com/Dodge), [Spot dodge](https://www.ssbwiki.com/Spot_dodge), [Roll](https://www.ssbwiki.com/Roll).
- State names: [fighter-states](./fighter-states.md). Conventions: [00-overview](./00-overview.md).

## pycats status

Implemented:
- **Shield** — `SHIELD_MAX_HP = 50` (config); held/regen tick in `pycats/entities/player.py`. ⚠ **Divergence:** pycats drains **0.2/frame and regens 0.2/frame** (symmetric, `SHIELD_DRAIN_PER_FRAME = 0.2`) vs PM's **0.28 drain / 0.07 regen** — a deliberate simplification to log at [#99](https://github.com/avidrucker/pycats/issues/99).
- **Shieldstun** — `pycats/combat/shield.py::shieldstun_frames` = `floor(damage × SHIELDSTUN_FACTOR)`, `SHIELDSTUN_FACTOR = 0.345`; locks the defender in shield via `Player.update`. ([#140](https://github.com/avidrucker/pycats/issues/140))
- **Shield break → dizzy** — `shield.py::shield_break_stun_frames` = `(400 − p) + 90` clamped `[SHIELD_BREAK_STUN_MIN = 90, MAX = 490]`. ([#12](https://github.com/avidrucker/pycats/issues/12))
- **Dodges** — spot / roll / air dodge in `pycats/entities/fighter_input.py`; `DODGE_TIME = 14`, `DODGE_SPEED = 14` (config), intangibility via the `invulnerable` flag.

**Deferred / divergent / open:**
- **Powershield / parry** — not implemented (deferred research, [#24](https://github.com/avidrucker/pycats/issues/24) thread c).
- **Shield poke geometry** — pycats uses circle hurtboxes; full poke geometry is approximate (see [combat-hitboxes-priority](./combat-hitboxes-priority.md)).
- **Shield pushback** magnitudes — deferred (refuted prior formula; [#24](https://github.com/avidrucker/pycats/issues/24) thread b).
- **Shield drain values** — 0.2/0.2 vs PM 0.28/0.07 (above).
- **Open decisions:** canonical dodge speed/duration ([#65](https://github.com/avidrucker/pycats/issues/65)); air-dodge commit-vs-redirect ([#66](https://github.com/avidrucker/pycats/issues/66)); air-dodge vertical-momentum cancel ([#23](https://github.com/avidrucker/pycats/issues/23)).
- Divergences: [#99](https://github.com/avidrucker/pycats/issues/99). Open questions: [#24](https://github.com/avidrucker/pycats/issues/24).
