# Brawl / Project M fighter states & interactions

> Research findings on whether a published list of SSBB / Project M fighter
> states and their interactions exists, and how collision/interaction
> resolution works (esp. shield vs. attack).
>
> Method: deep-research harness — 107 agents over 24 sources, 102 claims
> extracted, top 25 adversarially verified (24 confirmed, 1 refuted).
> Date: 2026-06-21.

## TL;DR

**Yes — an enumerated list of fighter *states* exists and is public. But there
is NO single published "state machine + interaction-resolution table."** The
flat list of action-state IDs is well documented; the *transitions* between
states and the *collision-resolution algorithm* live in code, not in any prose
document.

## Where the state list lives

Action states are enumerated with hex IDs across three corroborating sources:

- **OpenSA "Smash Engine Documentation" wiki** —
  [`Actions (Brawl)`](http://opensa.dantarion.com/wiki/Actions_(Brawl)) and
  [`StatusIDs`](http://opensa.dantarion.com/wiki/StatusIDs). Sortable table:
  Hex ID / Short Name / Description / Subactions Called.
- **[rukaidata.com](https://rukaidata.com/Brawl/)** — per-character data dumps
  (e.g. 263 action entries for Mario: `0x0 Wait`, `0x24 Jab`,
  `0x112 SpecialN`, `0x116 Final`).
- **[BrawlHeaders `fighter.h`](https://raw.githubusercontent.com/Sammi-Husky/BrawlHeaders/master/Brawl/Include/ft/fighter.h)**
  — the same enum in machine-readable C:
  `Fighter::Status::Kind { Wait=0x0 … Guard_On=0x1A … Guard_Damage=0x1D … Dead=0xBD }`.

### Shield states (contiguous block)

| Action ID | Name      | Meaning            |
| --------- | --------- | ------------------ |
| `0x1A`    | GuardOn   | Enter shield       |
| `0x1B`    | Guard     | Shielding          |
| `0x1C`    | GuardOff  | Exit shield        |
| `0x1D`    | GuardDamage | Shieldstun       |

⚠️ **Don't confuse *Action* IDs with *SubAction* (animation) IDs** — different
namespaces. GuardOn is `0x1A` as an action but `0x3F` as a subaction.

## Shield vs. attack hitbox (the original question)

The collision rule is **shield-priority** (confirmed 3-0, from
[SmashWiki Shield_poke](https://www.ssbwiki.com/Shield_poke) +
[Shield](https://www.ssbwiki.com/Shield)):

> If B's hitbox touches A's shield bubble **at all** → blocked. A enters
> shieldstun, shield loses HP. A **poke** (damage through the shield) happens
> only when the hitbox reaches an exposed hurtbox *without* touching the shield
> bubble.

So "enough shield durability left" is **not** the deciding factor for whether
contact is blocked — **geometry is**. The shield always wins the contact; HP
just determines how small the bubble has shrunk (and thus how much hurtbox
pokes out).

### Verified shield numbers (Brawl)

| Quantity          | Value                                   |
| ----------------- | --------------------------------------- |
| Max HP            | 50 (71.43 effective via 0.7× damage mult) |
| Depletion         | 0.28/frame (16.8/s)                     |
| Regen             | 0.07/frame (4.2/s)                      |
| Full-HP hold time | ~2.98 s                                 |
| Shieldstun        | `floor(damage × 0.345)` frames (<2.9% → 0 stun) |

## How interactions are actually modeled

Brawl doesn't use a numeric transition table — it uses an **event-based PSA
script system**: actions → subactions → 4 scripts each (Main/GFX/SFX/Other) →
lists of events, with **hitboxes spawned by hitbox-creation events**
([rukaidata writeup](https://github.com/rukai/rukaidata/blob/main/docs/writeup.md)).

Collision resolution is implemented as **separate observer interfaces** on the
`Fighter` class — `soCollisionShieldEventObserver`, `…Attack`, `…Hit`,
`…Reflector`, `…Absorber`, `…Search` (visible in `fighter.h`). Hurtboxes are
static stretched-sphere/capsule volumes on bones; hitboxes are runtime-created.

## Source of truth for internals

- **[doldecomp/brawl](https://github.com/doldecomp/brawl)** — active matching
  decompilation (USA Rev 2), reconstructing fighters under `src/mo_fighter`.
  **~1% complete**, so it doesn't yet expose the full collision algorithm.
- **[doldecomp/melee](https://github.com/doldecomp/melee)** — ~96% C, but a
  different engine; only analogous (PM is a *Brawl* mod, not Melee).

## Caveats & gaps

- ❌ **Shield pushback formulas were REFUTED** (1-2 vote) — the proposed
  `(damage×0.069+0.4)×shield` capped at 1.6 failed verification. Treat pushback
  magnitudes as **unestablished**.
- No published **state-to-state transition graph** (which action can legally go
  to which) — only the flat ID list exists.
- Shield numbers come from **SmashWiki** (datamined/measured community data) —
  reliable and cross-corroborated, but secondary-tier, not decompilation output.
- **Project M / Project+-specific** deviations (and its added powershield/parry)
  were only lightly corroborated via rukaidata Project+ frame data — no
  PM-specific authoritative state list found distinct from base Brawl.
- "Change shield density" (light shield) is **Melee-only**; doesn't apply to
  Brawl/PM.
- OpenSA/dantarion servers were slow/timing out; some confirmation relied on
  search-index snapshots and Wayback archives rather than live fetches.

## Best practical resources

- **Browse states & scripts per character:** [rukaidata.com](https://rukaidata.com/Brawl/)
- **Action ID reference:** [OpenSA `Actions (Brawl)`](http://opensa.dantarion.com/wiki/Actions_(Brawl))
- **Code-level truth:** [BrawlHeaders `fighter.h`](https://github.com/Sammi-Husky/BrawlHeaders)
- **Shield / shieldstun / poke mechanics:** [SmashWiki Shield](https://www.ssbwiki.com/Shield),
  [Shieldstun](https://www.ssbwiki.com/Shieldstun),
  [Shield_poke](https://www.ssbwiki.com/Shield_poke)

## Key sources

| Source | Quality | What it gives |
| ------ | ------- | ------------- |
| [doldecomp/brawl](https://github.com/doldecomp/brawl) | primary | Decompiled fighter logic (incomplete) |
| [BrawlHeaders](https://github.com/Sammi-Husky/BrawlHeaders) | primary | `fighter.h` state enum + collision observers |
| [rukaidata.com](https://rukaidata.com/Brawl/) | primary | Per-character actions/subactions/scripts |
| [OpenSA wiki](http://opensa.dantarion.com/wiki/Category:Brawl_Documentation) | primary | Action IDs, hitbox flags, hurtbox docs |
| [rukaidata writeup](https://github.com/rukai/rukaidata/blob/main/docs/writeup.md) | primary | How the PSA script/event model works |
| [SmashWiki Shield](https://www.ssbwiki.com/Shield) | secondary | Shield HP/depletion/regen numbers |
| [SmashWiki Shieldstun](https://www.ssbwiki.com/Shieldstun) | secondary | Shieldstun formula |
| [SmashWiki Shield_poke](https://www.ssbwiki.com/Shield_poke) | secondary | Shield-priority collision rule |
