# Hitboxes, hurtboxes, priority & staling — PM mechanics reference

> How Project M decides **whether** a hit connects (and which hit wins when
> several happen at once), as opposed to **how hard** it launches (that's
> [combat-knockback-hitstun](./combat-knockback-hitstun.md)). Part of the
> [PM mechanics reference](./00-overview.md) ([epic #147](https://github.com/avidrucker/pycats/issues/147));
> PM 3.6 values, Brawl/Melee deltas noted. Conventions (60 Hz integer frames,
> raw combat numbers, spatial × `PX_PER_UNIT ≈ 5.4`): see [00-overview](./00-overview.md).

**Audience:** a contributor — human or agent — about to implement or modify
hit-resolution. Reference depth, not a tutorial.

A hit lands when an attacker's **hitbox** overlaps a defender's **hurtbox** on the
same frame and the defender is vulnerable there. Around that core sit the rules
for moves with several hitboxes, for two attacks meeting in the air or on the
ground, and for the same move thrown over and over.

## The hitbox / hurtbox model

- Both are **collision shapes attached to the fighter's skeleton**, placed per
  frame. The base shape is a circle (offset + radius); in the real game a hitbox
  can be a stretched **capsule** (a swept circle between two bone points) so a
  fast limb doesn't tunnel between frames.
- **Hurtboxes** are the vulnerable regions (the body); **hitboxes** are the
  damaging regions (a swung limb/weapon). A move's hitboxes are only present
  during its **active frames** (see [moveset-and-frame-data](./00-overview.md)).
- Offsets are **facing-relative**: the same data mirrors when the fighter turns.
- A defender can be **intangible** (no hurtbox interaction — dodges, ledge/respawn
  invincibility) or have a hurtbox **shrunk/relocated** (e.g. a crouch lowers the
  profile so high attacks whiff). Geometry, not an HP check, decides contact —
  including against a shield (shield-poke geometry, see [defense-shield-dodge](./00-overview.md)).
- Resolution is **circle-vs-shape overlap** per frame; touching counts as overlap.

## Multi-hitbox moves & hitbox-id priority

A single move commonly declares **several hitboxes at once** — e.g. a sourspot near
the body and a sweetspot at the tip, each with its **own damage / angle / BKB /
KBG**. Two rules govern them:

1. **One connect per move, per target.** A move hits a given fighter **once**, even
   if two of its hitboxes overlap that fighter on the same frame — you don't take
   the sweetspot *and* the sourspot.
2. **Hitbox-id priority decides which one.** When several of a move's hitboxes
   overlap the target, the one with the **highest priority (lowest hitbox id)**
   applies. Move data is authored so the intended box (often the sweetspot) has
   priority. This is *intra-move* priority — distinct from clank below.

Hitboxes are also how a move connects with **multiple opponents** (each opponent
resolves independently) and across its active window (it can only rehit a target
after a per-move refresh interval — out of scope here).

## Clank / priority between opposing attacks

When **two opposing fighters' hitboxes overlap on the same frame**, PM resolves it
with a **deterministic rule called clank** — no randomness. The decision is made
purely from the two attacks' **damage**, using the **9% "priority range"**:

- **Damage within 9% of each other** (including *exactly equal*) → **both attacks
  cancel.** Neither connects; both fighters enter **rebound** (a brief bounce-back),
  shown as a white flash. (A same-time, same-damage trade is difference 0% → inside
  the window → both clank, no damage to either.)
- **One attack > 9% stronger** → the **stronger continues** normally; the **weaker
  ends** and that fighter rebounds.

Important qualifiers:

- **Aerials do not clank.** The priority system is for **ground** attacks (and
  ground-vs-projectile). An aerial passing through a ground hitbox just trades.
- **Transcendent priority:** some moves (and most projectiles vs each other) have a
  per-move flag that lets them **pass through without clanking** — still
  deterministic, not RNG.
- The rebound carries **freeze frames equal to the stronger attack's hitlag** (ties
  clank to [hitlag](./combat-knockback-hitstun.md)).

## Stale-move negation

Repeating the **same move** makes it progressively **weaker** (less damage → less
knockback), which discourages spamming one kill move and rewards varied combos.

- The game keeps a small **staleness queue** of the most recently *landed* moves
  (≈ the last 9). A move's damage is reduced by an amount that grows with **how
  many copies of it are in the queue** (most-recent copies weighted heaviest).
- Landing **other** moves pushes the stale move out of the queue, **refreshing** it
  back toward full power.
- Both the **damage** and the resulting **knockback** scale down (knockback uses
  the staled damage in the formula), so staling shifts kill percents.
- Only moves that **connect** stale (whiffs don't), and it tracks **per move**.

## Brawl / Melee deltas

- **Priority range:** 9% across Melee → Brawl → PM (the original SSB64 used 10%).
- **Clank-frame hits:** in Melee the stronger move can still hit the weaker user on
  or right after the clank frame; later games shield that frame. Behaviour here is
  the PM/Brawl family rule.
- **Stale-move queue:** present Melee-onward; exact depth/weights vary by game
  (~9 entries in the Brawl/PM family).
- **Hitbox-radius unit:** Melee radii are 256× a smaller unit (divide before
  comparing); Brawl/PM use the standard unit (see [00-overview](./00-overview.md)).

## Sources

- SmashWiki — [Priority](https://www.ssbwiki.com/Priority), [Rebound](https://www.ssbwiki.com/Rebound), [Hurtbox](https://www.ssbwiki.com/Hurtbox), [Hitbox](https://www.ssbwiki.com/Hitbox), [Stale-move negation](https://www.ssbwiki.com/Stale-move_negation), [Priority#Transcendent_priority](https://www.ssbwiki.com/Priority).
- [`docs/research-findings-141-clank-priority-simultaneous-trade-dragonfruit-2026-06-26.md`](../research-findings-141-clank-priority-simultaneous-trade-dragonfruit-2026-06-26.md) — the clank/9% rule, on-target answer + pycats mapping.
- Conventions: [`00-overview.md`](./00-overview.md).

## pycats status

Implemented (Phase 1 [#38](https://github.com/avidrucker/pycats/issues/38) + Phase 2 [#142](https://github.com/avidrucker/pycats/issues/142)):
- **Hit/hurtbox geometry** — circle-vs-circle overlap, facing-relative, per frame, in `pycats/systems/combat.py::process_hits` + `pycats/combat/geometry.py` (`resolve_circle`, `circle_overlap`). Crouch swaps to a lower hurtbox ([#124](https://github.com/avidrucker/pycats/issues/124)); intangibility via the dodge/respawn `intangible` flag. Hurtboxes are circles, **not capsules** (approximation).
- **Multi-hitbox + id-priority + one-connect** — a `MoveData` carries a hitbox tuple; `process_hits` walks them in **priority order (tuple order)** and applies the **first** overlap, once per target. `Attack.resolved` holds the resolved circles. ([#130](https://github.com/avidrucker/pycats/issues/130))
- **Clank / 9% priority** — opposing active **ground** hitboxes within `CLANK_PRIORITY_RANGE = 9`% both end, else the stronger continues; aerials are exempt via `Attack.in_air`. In `process_hits`'s clank pass. ([#133](https://github.com/avidrucker/pycats/issues/133))
- **Move selection** (which hitbox set a press produces) — `pycats/combat/move_select.py` ([#143](https://github.com/avidrucker/pycats/issues/143)).

**Deferred / divergent in pycats:**
- **Stale-move negation** — *not implemented* (a planned Phase-2 slice on [#142](https://github.com/avidrucker/pycats/issues/142)); moves never weaken from repetition yet.
- **Rebound state / animation** — a clank currently just **negates** the losing hitbox (no bounce-back state or clank freeze-frames); rebound is a later state.
- **Capsule (swept) hitboxes** — circles only; fast limbs can in principle tunnel.
- **Transcendent priority** — no per-move flag; not modelled (no projectiles yet).
- **Per-hitbox temporal windows** — one startup/active/recovery per `MoveData`, so *sequential* multi-hit moves (jab1-2-3, rapid jab, multi-hit aerials) can't yet be expressed (schema gap).
- Open questions: [#24](https://github.com/avidrucker/pycats/issues/24); divergences logged at [#99](https://github.com/avidrucker/pycats/issues/99).
