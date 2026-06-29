# Project M mechanics reference — overview

> Entry point for the **PM mechanics reference** ([epic #147](https://github.com/avidrucker/pycats/issues/147)):
> a set of markdown docs, one per sub-domain, **describing how Project M actually
> works**. This file sets the conventions every other doc inherits, the source
> list, and the index.
>
> **Scope of the set:** *descriptive reference of the real game*, so a contributor
> (human or agent) can learn a sub-domain before implementing it. It is **not**:
> - the pycats implementation roadmap → `docs/research/pm-mechanics-implementation-analysis.md`,
> - the open-research-questions tracker → [#24](https://github.com/avidrucker/pycats/issues/24),
> - the intentional-divergence log → [#99](https://github.com/avidrucker/pycats/issues/99) (`docs/project-m-parity.md`, pending #99).

## What Project M is

**Project M (PM)** is a community mod of **Super Smash Bros. Brawl** (Wii, 2008)
that retunes Brawl toward *Melee*-style movement and competitive play. It runs on
**Brawl's engine**, so its low-level model (action states, the knockback formula,
shield rules, 60 Hz timing) is Brawl's; PM **rebalances values** (attributes,
frame data, shieldstun) and **adds** mechanics (wavedash, L-cancel, powershield/
parry, extra movement tech).

**Canonical version: PM 3.6.** All values in this reference are PM 3.6 unless
noted (see [[pm36-canonical-reference]] memory and the unit doc #120). Where a
mechanic is identical across the family we say "Brawl/PM"; where PM diverges from
base Brawl, or 3.6 from Project+, we call it out.

Engine lineage for formulas: the **knockback formula is unchanged from Melee
onward** (Melee → Brawl → PM are one family), so raw BKB/KBG/weight/damage feed it
directly — but PM **rebalanced the inputs**, so per-character/​per-move *numbers*
differ from Melee and Brawl.

## Conventions every reference doc follows

### Timing — 60 Hz fixed timestep
PM is locked to a **fixed 60 FPS** (NTSC); simulation and display advance on the
same clock, **one game tick per displayed frame**. There is no variable frame rate
and no simulation/render split — physics, hitboxes, knockback, shield decay, and
intangibility windows are computed once per frame. 60 is the ceiling, not a
guaranteed floor: an overloaded scene slows the **whole game** down in lockstep,
then recovers. **All frame data is therefore integer frames** (startup/active/
recovery, hitstun, shieldstun, intangibility). The PAL build runs at 50 Hz (out of
scope; PM inherits the NTSC 60 Hz model).
→ Full treatment: [`docs/research/pm-framerate-fidelity.md`](../research/pm-framerate-fidelity.md).

### Units — raw combat numbers, one spatial scale
- **Combat numbers drop in raw** — frames, damage %, weight, BKB, KBG, and launch
  angle mean the same thing here as in PM (the knockback formula is verbatim).
- **Spatial values use one scale.** PM positions/sizes/speeds are in abstract
  "units" (1 unit ≈ a decimetre); there is no canonical unit→pixel mapping in the
  games. pycats adopts **`PX_PER_UNIT ≈ 5.4`** (reverse-derived from PM Mario's
  gravity/walk/jump landing on pycats' existing globals). Spatial reference values
  in these docs are given raw, with the ×5.4 conversion noted.
- **Angle sentinels are codes, not degrees** — e.g. **361** = the Sakurai angle,
  365/366 = autolink — handle explicitly when porting.
- **Melee hitbox-radius quirk:** Melee hitbox radii are 256× a smaller unit;
  divide by 256 before comparing to Brawl/PM. (Brawl/PM use the standard unit.)
→ Full treatment: [`docs/research-120-smash-units-and-sources.md`](../research-120-smash-units-and-sources.md).

### Per-doc template
Each sub-domain doc should follow:
1. **Intro** — one-paragraph scope + how it fits PM.
2. **Sections** — the mechanics, with PM 3.6 values (raw; spatial × 5.4 noted),
   formulas with constants, and Brawl/Melee deltas where relevant.
3. **Sources** — primary citations (see below).
4. **pycats status** — a footer linking where pycats implements it, the parity
   divergences ([#99](https://github.com/avidrucker/pycats/issues/99)), and any
   open questions ([#24](https://github.com/avidrucker/pycats/issues/24)).

Docs **cite and fold in** the existing `docs/research/*` findings rather than
duplicating them.

## Primary sources

| Source | Best for | Notes |
|---|---|---|
| [rukaidata.com — PM 3.6](https://rukaidata.com/PM3.6/) | Moves / hitboxes (damage, BKB, KBG, angle, hitbox id/size) | ⭐ Primary; datamined from `.pac` via open-source [`brawllib_rs`](https://github.com/rukai/rukaidata). |
| [SmashWiki PM character pages](https://www.ssbwiki.com/Mario_(PM)) | Attributes (weight, walk/dash/air, gravity, fall, jumps) + move cross-check | ⭐ Primary; community-datamined, human-readable. |
| [SmashWiki](https://www.ssbwiki.com/) (Knockback, Hitstun, Hitlag, Shieldstun, Priority, …) | Mechanic formulas + definitions | Engine-family reference (Melee→Ultimate). |
| [OpenSA / dantarion](http://opensa.dantarion.com/wiki/Actions_(Brawl)), Brawl decomp | Action-state IDs, engine internals | State/transition reference. |
| pmunofficial.com, Smashboards PM 3.5/3.6 threads | PM-specific changes | Secondary cross-check. |

For a fully-automated data dump, run `brawllib_rs` against PM 3.6 `.pac` files to
emit structured JSON. Ranked source detail (incl. Melee/Brawl fallbacks): #120.

## Index — sub-domain docs

Status: ✅ written · ⬜ planned ([epic #147](https://github.com/avidrucker/pycats/issues/147) files each as its own ticket, one at a time).

| Doc | Sub-domain | Status |
|---|---|---|
| `00-overview.md` | This file — conventions, sources, index | ✅ |
| [`combat-knockback-hitstun.md`](./combat-knockback-hitstun.md) | Knockback formula, hitstun, hitlag, launch+decay, DI/SDI, angles | ✅ |
| [`combat-hitboxes-priority.md`](./combat-hitboxes-priority.md) | Hit/hurtbox model, multi-hitbox, clank/priority, stale-move negation | ✅ |
| [`fighter-states.md`](./fighter-states.md) | Action-state graph + transitions | ✅ |
| [`movement-and-tech.md`](./movement-and-tech.md) | Walk/dash/run, jumps, fast-fall, wavedash, dash-dance, pivot, L-cancel | ✅ |
| [`defense-shield-dodge.md`](./defense-shield-dodge.md) | Shield (HP/drain/shieldstun/poke/powershield/parry), spot/roll/air dodge | ✅ |
| [`grabs-throws.md`](./grabs-throws.md) | Grab, pummel, throws, release, mash-escape | ✅ |
| [`ledge-mechanics.md`](./ledge-mechanics.md) | Ledge grab/hang, getup, invincibility, edgeguarding, teching | ✅ |
| [`character-data-and-archetypes.md`](./character-data-and-archetypes.md) | Per-character attributes, geometry, frame-data structure, roster/archetypes | ✅ |
| [`moveset-and-frame-data.md`](./moveset-and-frame-data.md) | Move taxonomy + per-move frame-data fields, charge moves, projectiles | ✅ |
| `stages-and-environment.md` | Stages, platform types, blast zones, ledges, camera | ⬜ |
| `menus-and-game-flow.md` | CSS, stage select, ruleset/match settings, results, options | ⬜ |
| `items.md` | PM item set + behaviour (low priority; pycats has no items) | ⬜ |

## pycats status

- **Implemented so far:** the combat core (Phase 1, [#38](https://github.com/avidrucker/pycats/issues/38)) — knockback + hitstun, multi-hitbox + clank, hitlag, ground/air split, shieldstun; and the moveset seam (Phase 2, [#142](https://github.com/avidrucker/pycats/issues/142)). These are the docs to write first.
- **Roadmap:** `docs/research/pm-mechanics-implementation-analysis.md` (phased plan).
- **Divergences:** [#99](https://github.com/avidrucker/pycats/issues/99) (will live at `docs/project-m-parity.md`).
- **Open questions:** [#24](https://github.com/avidrucker/pycats/issues/24).

## Sources

- [`docs/research/pm-framerate-fidelity.md`](../research/pm-framerate-fidelity.md) — 60 Hz fixed timestep, integer frames.
- [`docs/research-120-smash-units-and-sources.md`](../research-120-smash-units-and-sources.md) — unit convention, `PX_PER_UNIT ≈ 5.4`, raw-combat rule, ranked source list.
- SmashWiki; rukaidata PM 3.6; the existing `docs/research/*` findings.
