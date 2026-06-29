# Moveset & frame data — PM mechanics reference

> The **move taxonomy** (what attacks a fighter has) and the **frame-data fields**
> that define each one. Companion to
> [character-data-and-archetypes](./character-data-and-archetypes.md) (which carries
> a character's *attributes/geometry* and defers move values here). This doc owns
> move *categories* + field *semantics*; how a move's hitbox **resolves** is in the
> combat docs, and per-character *values* live in the character doc — linked, not
> restated. Part of the [PM mechanics reference](./00-overview.md)
> ([epic #147](https://github.com/avidrucker/pycats/issues/147)); PM 3.6.

**Audience:** a contributor — human or agent — about to author or tune a move, or
implement a move category. Reference depth, not a tutorial; assumes the
[00-overview](./00-overview.md) conventions (60 Hz integer frames).

## Move taxonomy

Every fighter's kit is built from a fixed set of input-addressed slots (the
input→slot mapping is [00-overview](./00-overview.md)'s seam; here's what fills them):

- **Normals (A):** **jab** (often a 1-2-3 or rapid multi-hit), **tilts** (forward /
  up / down), **dash attack** (A while dashing).
- **Smashes (A + flick / charge):** forward / up / down — **chargeable** (hold to
  build power, release to fire), often **angleable** (f-smash); the KO tools.
- **Aerials (A in the air):** **n-air, f-air, b-air, u-air, d-air** (some, like
  Mario's d-air, are **multi-hit**).
- **Specials (B):** **neutral-B, side-B, up-B, down-B** — the toolbox: projectiles,
  command grabs, reflectors, and **up-B recovery** moves.
- **Grabs & throws:** grab → pummel → forward/back/up/down throw — see
  [grabs-throws](./00-overview.md).

## Per-move frame-data fields

A move is, at heart, a timeline of states plus its hitbox data. The fields:

- **startup** — frames before the first hitbox is active (commitment / how
  punishable it is on whiff).
- **active** — frames the hitbox(es) are present.
- **recovery (endlag)** — frames after the active window before the fighter is free.
- **IASA** ("interruptible as soon as") — a frame within recovery after which you
  may act early (cancel into another action); shortens *effective* endlag.
- **autocancel windows** — frame ranges of an aerial in which landing incurs
  **no** landing lag (e.g. early-rise or late-fall of the move).
- **landing lag** — endlag if you land *during* an aerial (outside autocancel);
  **L-cancel** (a well-timed shield press before landing) **halves** it — see
  [movement-and-tech](./movement-and-tech.md).
- **per-hitbox data** — each active hitbox carries damage, angle (incl. sentinels
  like 361), BKB, KBG, and its circle (offset+radius); *how* these resolve is in
  [combat-knockback-hitstun](./combat-knockback-hitstun.md) +
  [combat-hitboxes-priority](./combat-hitboxes-priority.md) (incl. **hitbox-id
  priority** and the one-connect rule).
- **multi-hit timing** — a move may have **simultaneous** hitboxes (a sweet/sour
  spot pair on the same frames) **and/or sequential** hits (jab1→jab2→jab3, a
  rapid jab, a multi-hit d-air) — separate active windows within one move.
- **hitlag / shieldstun multipliers** — per-move tweaks to the freeze/block-stun
  (default 1×) — see [combat-knockback-hitstun](./combat-knockback-hitstun.md).

Worked example (PM Mario down-tilt, `AttackLw3`): startup 5 / active 4 (frames 5–8)
/ recovery to ~30 total; **3 simultaneous hitboxes** dealing 9/9/8, BKB 30, KBG 80,
angle 80°. Full kit damage table: see [research-spec-119](../research-spec-119-mario-cat-pm.md).

## Charge moves

Smashes (and some specials, e.g. a chargeable projectile) have a **charge phase**:
hold the input to accumulate charge frames (scaling damage/knockback up to a cap),
then release to enter the normal startup→active→recovery. Some specials **store**
charge between uses. Charge adds a state before startup; it doesn't change how the
eventual hitbox resolves.

## Projectiles

A projectile is a **separate entity** the move spawns, not a hitbox fixed to the
fighter: it has its **own position, velocity, and lifetime** and travels
independently (Mario's Fireball, Fox's blaster shot). It still carries normal
hitbox data (damage/angle/BKB/KBG) and resolves against hurtboxes the same way —
the difference is that it **moves** and persists after the move's active frames.
Reflectors/absorbers interact with projectiles specifically.

## Brawl / Melee / PM deltas

- **L-cancel:** present in Melee, **removed in base Brawl, restored by PM** — a core
  reason PM aerials are safe/combo-heavy.
- **IASA / autocancel:** universal frame-data concepts; PM's *values* differ from
  Brawl/Melee per its rebalance.
- **Frame-data values are PM-specific** — use PM 3.6 sources (rukaidata PM3.6,
  SmashWiki PM pages), not Melee/Brawl, where they differ.
- **Stale-move negation** weakens a repeated move's damage/KB — documented in
  [combat-hitboxes-priority](./combat-hitboxes-priority.md) (look there if "my move
  got weaker").

## Sources

- [`docs/research-spec-119-mario-cat-pm.md`](../research-spec-119-mario-cat-pm.md) — the full Mario kit table + a worked down-tilt (frame data dropped in raw).
- [rukaidata PM 3.6](https://rukaidata.com/PM3.6/) per-subaction frame data; SmashWiki — [Frame data](https://www.ssbwiki.com/Frame_data), [Auto-cancel](https://www.ssbwiki.com/Auto-cancel), [Interruptibility](https://www.ssbwiki.com/Interruptibility), [L-canceling](https://www.ssbwiki.com/L-canceling).
- Hit resolution: [combat-knockback-hitstun](./combat-knockback-hitstun.md), [combat-hitboxes-priority](./combat-hitboxes-priority.md). Conventions: [00-overview](./00-overview.md).

## pycats status

Schema & seam:
- **`pycats/combat/data.py`** — `MoveData(name, in_air, startup, active, recovery, hitboxes)`; total duration = startup+active+recovery; `hitboxes` is a tuple (multi-hitbox).
- **`pycats/combat/move_select.py`** — the input→move-key seam (`jab`/`ftilt`/`utilt`/`dtilt`/`nair`/`fair`/`bair`/`uair`/`dair`/`neutral_b`/`side_b`/`up_b`/`down_b`, with `attack` the neutral-ground alias) ([#143](https://github.com/avidrucker/pycats/issues/143)).
- **`pycats/combat/move_clock.py`** — drives startup→active→recovery and spawns the hitbox set on the active frame ([#71](https://github.com/avidrucker/pycats/issues/71)).

Implemented:
- Single + **simultaneous multi-hitbox** moves ([#130](https://github.com/avidrucker/pycats/issues/130)); ground/air split; the live Nalio moves — **d-tilt** (real 3-box) + **n-air** (clean-hit) in `pycats/characters/nalio_cat.py`.

**Deferred / divergent:**
- **Smashes + charge**, **dash attack** (needs a dash state), **the rest of the tilts/aerials**, and **specials** beyond the wired B button — Phase 2 epic [#142](https://github.com/avidrucker/pycats/issues/142).
- **Projectiles** — `Attack` is static (fixed at spawn); no traveling-entity system (shared Fireball/blaster gate).
- **IASA / autocancel / landing lag / L-cancel** — no landing-lag system yet (L-cancel gated on [#24](https://github.com/avidrucker/pycats/issues/24) thread c).
- **Sequential multi-hit windows** — one startup/active/recovery per `MoveData`, so jab1-2-3 / rapid jab / multi-hit d-air can't be expressed yet (**schema gap**; needs move-chaining or per-hitbox timing).
- Divergences: [#99](https://github.com/avidrucker/pycats/issues/99). Open questions: [#24](https://github.com/avidrucker/pycats/issues/24). Roadmap: `docs/research/pm-mechanics-implementation-analysis.md` (Phase 2).
