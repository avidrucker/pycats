# Where to find source data — the PM data-sourcing map (living)

> **Audience:** an agent or contributor who needs the authoritative source for a
> value **before** changing it (RULES → "Changing values") — the first stop when a
> number needs a basis. It answers one question: *"for data type X, what is the
> correct/accurate source, and is it online-only or cloned locally?"*
>
> This is the **decision map + availability tracker**. The deep, per-source list
> lives in [`../research-120-smash-units-and-sources.md`](../research-120-smash-units-and-sources.md)
> (#120) — read that for the sources themselves; read this to pick the right one
> and know whether it's reachable offline yet.
>
> **Living doc:** the "Local clones" tracker below flips rows from ⏳ online-only to
> ✅ offline-available as clone tickets (#614 / #616 and future ones) land. Keep it
> current when a clone lands. Related: [[rukaidata-engine-hardcoded-limit]],
> [[pm36-canonical-reference]].

## Why there is no single source

Project M is a **Brawl mod that restored much Melee behavior**, so an engine value
can originate in any of three lineages — Melee (restored by PM), base Brawl, or a
PM-specific override. There is **no one datamining tool** that exposes all of them.
Triage by **where the value originated**, then go to that lineage's authoritative
source.

## 1. Decision tree — engine-hardcoded globals by origin

Engine globals (gravity, air-dodge force, L-cancel factor, the smash-charge
multiplier, …) are **not** in the per-move scripts. Route the question by origin:

| The global is… | Authoritative source | Example |
|---|---|---|
| **Melee-inherited** (PM restored it) | `doldecomp/melee` decompilation (model/logic) + a faithful reimpl for the literal: **meleelight** (JS), or Melee `PlCo.dat` offsets via the Magus "SSBM Data Sheet" | air-dodge `escapeair_force = 3.1`; smash multiplier **1.3671** |
| **Brawl-base, scripted per-move** | **rukaidata / brawllib_rs** | hitbox BKB/KBG/angle/size |
| **Brawl-base engine action/state** | **OpenSA / dantarion** (Brawl actions), SmashWiki Brawl | action IDs, intangibility windows |
| **PM-specific override** | PMDT **changelogs** (*what*) + PM **codeset/GCT** (*how*) + **Project+** source | a 59-frame smash charge, if real ⚠ |

> ⚠ The "59-frame smash charge" row is an **example of an unconfirmed claim**, not a
> stated fact — verify against a PM changelog/codeset before citing it.

## 2. Data-type → source table (with online/offline availability)

| Data type | Best source | Tier | Online now | Offline (local clone) |
|---|---|---|---|---|
| Move/hitbox data (damage, BKB, KBG, angle, size, positions, scripted self-vel) | rukaidata.com / brawllib_rs | ⭐ primary for moves | rukaidata.com (HTML/bincode) ⚠ | ✅ `~/Documents/Study/Rust/brawllib_rs/` (#614) |
| Melee-inherited engine literals (air-dodge, L-cancel, smash multiplier…) | meleelight (JS reimpl), doldecomp/melee | primary literal / model | github (schmooblidon/meleelight) ⚠ | ✅ `~/Documents/Study/JavaScript/meleelight/` (#616) |
| Brawl engine actions/states | OpenSA / dantarion, SmashWiki Brawl | engine/state ref | opensa.dantarion.com ⚠ | — |
| PM-specific overrides / changes | PMDT changelogs, PM codeset, Project+ | authoritative for *what changed* | pmunofficial.com / Smashboards / Project+ repos ⚠ | — |
| Mechanics prose / cross-checks | SmashWiki (Smash attack, Charge, Project M pages) | secondary, citable | ssbwiki.com | — |

⚠ = URL/mirror status **to-verify** (see "To-verify" below). Confidence, not
guesses-as-facts.

## 3. How to get PMDT data (three channels)

1. **Changelogs** — PMDT patch notes (projectmgame.com archives / pmunofficial.com /
   Smashboards changelog threads). Authoritative for *what* changed.
2. **The PM build** — the `.pac` files (move data → readable via brawllib_rs)
   **plus** the codeset/GCT (Gecko codes + custom PSA/ASM = the *engine* changes).
   Engine globals live in the codeset, **NOT** in the `.pac`.
3. **Project+** — the more-open community continuation of PM; usually the most
   accessible primary for PM-lineage engine logic. PM itself was **never fully
   open-sourced** (Nintendo C&D, 2015), so Project+ is often the closest reachable
   primary.

## 4. Key limits to state plainly

- **rukaidata / brawllib_rs do NOT expose engine globals** — only the per-move
  subaction scripts (established #215 / #222; the `DODGE_AIR_SPEED` case). An
  engine-global question routed to rukaidata comes back empty; route it to the
  decision tree in §1 instead. See [[rukaidata-engine-hardcoded-limit]].
- **SmashWiki is citable secondary** (the tier the repo already uses), but a
  PM-specific number should prefer the **PM-specific** page/changelog over a general
  Melee/Brawl value applied to PM. A Melee literal is only authoritative for a
  value PM actually inherited unchanged.

## Local clones

The offline mirrors of the sources above. Each row lists the source, its local
path, and what it is authoritative for. Clone tickets flip a row from ⏳ pending to
✅ available when they land — **update this section when a clone lands.**

| Source | Local path | Authoritative for | Status |
|---|---|---|---|
| brawllib_rs | `~/Documents/Study/Rust/brawllib_rs/` | Brawl-base scripted per-move data (hitbox BKB/KBG/angle/size, scripted self-vel) | ✅ available (#614) |
| meleelight | `~/Documents/Study/JavaScript/meleelight/` | Melee-inherited engine literals (air-dodge, L-cancel, smash multiplier) as a faithful JS reimpl | ✅ available (#616) |

## To-verify

This doc records **confidence, not certainty**. The following are unconfirmed and
marked ⚠ above; firm them up via a dedicated spike (**TBD — file before firming any
URL**, so the ⚠ marks have an owner and don't rot as permanent unknowns):

- Exact URLs / mirror hosts for the Project+ repos and the PMDT changelog host.
- Whether rukaidata.com / opensa.dantarion.com / the meleelight repo path are
  current (link-rot check).
- The "59-frame smash charge" example (§1) — confirm against a PM changelog/codeset
  or drop it.

## Refs

- Tiered sourcing worked out: #595 / #599.
- Engine-global limit (`DODGE_AIR_SPEED`, why rukaidata can't answer): #215 / #222.
- Clone tickets tracked above: #614 (brawllib_rs), #616 (meleelight).
- Deep sources list: [`../research-120-smash-units-and-sources.md`](../research-120-smash-units-and-sources.md) (#120).
- Memory: [[rukaidata-engine-hardcoded-limit]], [[pm36-canonical-reference]].
