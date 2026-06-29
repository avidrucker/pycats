# Character data & archetypes — PM mechanics reference

> What **data defines a fighter** in Project M, and how a roster of distinct
> characters is built from those same fields. This doc owns the **data model +
> roster concept**; the mechanic *formulas* live in their own docs (linked), and
> the full per-move tables live in [moveset-and-frame-data](./00-overview.md).
> Part of the [PM mechanics reference](./00-overview.md)
> ([epic #147](https://github.com/avidrucker/pycats/issues/147)); PM 3.6,
> values via the [00-overview](./00-overview.md) unit convention.

**Audience:** a contributor — human or agent — about to add or tune a character's
data (attributes, geometry, frame data) or implement a new archetype. Reference
depth, not a tutorial.

A PM character is **almost entirely data**: a set of numbers + collision shapes +
a move table fed into one shared engine. Two characters differ only in those
values — there is no per-character physics code. So "design a fighter" = "choose
this data."

## Attribute dimensions

The scalar attributes that define how a fighter *moves and survives* (values are
PM units; × `PX_PER_UNIT ≈ 5.4` for pixels — see [movement-and-tech](./movement-and-tech.md) for the model):

| Dimension | What it controls |
|---|---|
| **Weight** | resistance to knockback (heavier = launched less, dies later) — the only defender term in the KB formula |
| **Walk / dash / run speed** | ground mobility |
| **Air speed / drift** | horizontal air control |
| **Gravity** | fall acceleration |
| **Fall speed / fast-fall** | terminal descent (fast-fallers fall harder, die off the top earlier) |
| **Jump count & heights** | short hop, full hop, number of mid-air jumps |
| **Air mobility** | how sharply drift can change direction |

These feed the mechanics documented elsewhere: weight →
[combat-knockback-hitstun](./combat-knockback-hitstun.md); speeds/jumps/gravity →
[movement-and-tech](./movement-and-tech.md).

## Geometry — per character

Body and collision shapes are **character-specific** (a tall swordfighter and a
round puffball have very different boxes):

- **Body / ECB size** — the fighter's footprint.
- **Hurtboxes** — the vulnerable regions, as **circles/capsules** (offset + radius)
  attached to the skeleton; bigger/​taller bodies are easier to hit.
- **Hitbox geometry** — each move's damaging circles have per-character offsets and
  radii (a disjointed character's hitboxes extend **beyond** the hurtbox — the
  "disjoint"). See the box model in
  [combat-hitboxes-priority](./combat-hitboxes-priority.md).

All spatial values are PM units × 5.4 for pixels.

## Frame-data structure (character level)

Each character carries a **move table**: a map of move slot → its frame data.
The *structure* of one entry (the fields; full values are
[moveset-and-frame-data](./00-overview.md)'s job):

- **timing:** `startup` / `active` / `recovery` (whole 60 Hz frames),
- **one or more hitboxes**, each with: damage, angle (incl. sentinels like 361),
  base knockback (BKB), knockback growth (KBG), and its circle (offset + radius),
- **flags:** grounded vs aerial, and (per move) properties like multi-hit windows.

So a character = attributes + geometry + this move table. A worked example
(PM Mario down-tilt, the data that drops in raw): damage 9/9/8 across 3 hitboxes,
BKB 30, KBG 80, angle 80°, active frames 5–8 — see
[combat-hitboxes-priority](./combat-hitboxes-priority.md) for how the 3 boxes
resolve and [moveset-and-frame-data](./00-overview.md) for the field semantics.

## Weight classes & the roster

Weight is the headline differentiator (Mario = **100**, the reference). Lighter
characters are comboed and KO'd earlier but are often faster; heavier characters
survive longer but are slower and easier to combo. A roster spreads characters
across weight × mobility × range × KO-power × projectile to create distinct
**archetypes** — recurring design templates:

- **all-rounder** (balanced baseline),
- **disjointed spacer** (reach beyond the hurtbox, tipper sweetspots, no projectile),
- **floaty featherweight** (multi-jump, weak KO, easy to launch),
- **heavyweight bruiser** (big hurtbox, heavy hits, strong throws, dies late),
- **fast-faller rushdown** (fastest run+fall, low-KB multi-hits, a projectile, dies early off the top).

### The 5 pycats archetypes

pycats maps five **cats** onto five PM archetypes (the archetype is mechanical; the
look stays feline). The archetype *concept* is PM; the cat names are the pycats
mapping ([#117](https://github.com/avidrucker/pycats/issues/117)):

| Cat plays as | Archetype | Weight | Signature |
|---|---|---|---|
| **Nalio** | Mario — all-rounder | medium (100) | versatile combo+KO baseline |
| (TBD) | Marth — disjointed spacer | light-med | disjoint reach + tipper, no projectile |
| (TBD) | Kirby — floaty featherweight | lightest | multi-jump (5–6), weak KO |
| (TBD) | Donkey Kong — heavyweight | heaviest | big hurtbox, heavy hits, strong throws |
| (TBD) | Fox — fast-faller rushdown | light | fastest run+fall, blaster, dies early |

## Brawl / Melee / PM deltas

- **PM rebalanced attributes & frame data** vs Brawl (and vs Melee) — the *formula*
  family is shared, but per-character *numbers* are PM-specific; use PM 3.6 sources
  ([#120](https://github.com/avidrucker/pycats/issues/120)), not Melee/Brawl, where they differ.
- **Weight scale** is consistent across the family (Mario ≈ 100); Mario is coded 98
  in some later builds / 95 in Project+ — pycats uses **PM 3.6 = 100**.
- Hitbox-radius unit: Melee 256× quirk (divide before comparing); Brawl/PM standard
  (see [00-overview](./00-overview.md)).

## Sources

- [`docs/research-spec-119-mario-cat-pm.md`](../research-spec-119-mario-cat-pm.md) — a full worked Mario → pycats character (attributes + down-tilt) example.
- [`docs/research-120-smash-units-and-sources.md`](../research-120-smash-units-and-sources.md) — unit convention + ranked PM data sources (rukaidata PM3.6, SmashWiki PM pages).
- SmashWiki PM character pages (e.g. [Mario (PM)](https://www.ssbwiki.com/Mario_(PM))); [rukaidata PM 3.6](https://rukaidata.com/PM3.6/).
- Conventions: [00-overview](./00-overview.md).

## pycats status

Schema & data:
- **`pycats/combat/data.py`** — `FighterData` carries `weight` (default 100),
  `gravity` / `max_fall_speed` / `move_speed` / `jump_vel` / `max_jumps`
  ([#126](https://github.com/avidrucker/pycats/issues/126)), `crouch_size` /
  `crouch_hurtbox` ([#124](https://github.com/avidrucker/pycats/issues/124)),
  a `hurtbox` (`Hurtbox` of `Circle`s), and a `moves` dict of `MoveData`
  (`Hitbox`/`Circle`). `load_fighter_data(key)` is the per-character seam.
- **Live characters:** `pycats/characters/nalio_cat.py` (Nalio = Mario archetype —
  per-char weight 100 + movement constants + the real 3-box down-tilt + neutral-air),
  `default_cat.py` (the baseline the sim/golden path uses).

**Implemented vs deferred:**
- ✅ Nalio (Mario archetype) data; per-character weight + movement constants ([#123](https://github.com/avidrucker/pycats/issues/123)/[#126](https://github.com/avidrucker/pycats/issues/126)).
- ⬜ The other **four archetypes** (Marth/Kirby/DK/Fox) — the [#117](https://github.com/avidrucker/pycats/issues/117) epic, populated as the moveset mechanics land ([#142](https://github.com/avidrucker/pycats/issues/142)).
- ⬜ **Capsule hurtboxes / full datamined geometry** — pycats uses a 2-circle body approximation, not per-character datamined capsules.
- Divergences (e.g. Mario weight 100): [#99](https://github.com/avidrucker/pycats/issues/99). Open questions: [#24](https://github.com/avidrucker/pycats/issues/24).
