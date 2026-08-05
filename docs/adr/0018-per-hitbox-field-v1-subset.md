# ADR-0018 — per-hitbox field set: the concrete V1 vs post-V1 subset

- **Status:** Accepted  *(2026-08-04 — owner ruling on #1161, in a wayfinder grilling session)*
- **Date:** 2026-08-04

## Context

[ADR-0017](./0017-store-what-the-engine-consumes-per-hitbox-field-principle.md) fixed the
**principle** (A): store only per-hitbox datamine fields the engine consumes (plus what the
editor must display); defer inert fields (post-V1) and re-pull from the live datamine when the
engine grows to need them. ADR-0017 part (b) — the concrete **per-field subset** — was delegated
to research (#1160) and this decision (#1161), both children of the datamined per-hitbox move
data map (#1147).

[#1160's findings doc](../research/2026-08-03-datamine-per-hitbox-mechanics-engine-roles.md)
established, per field, the real mechanic (primary-sourced against `struct HitBoxValues` in
`brawllib_rs/src/high_level_fighter.rs` and the KB/hitlag reference), whether pycats consumes it
today, and the cost to consume. This ADR records the field-by-field ruling made on top of those
findings.

Already stored + consumed (out of scope, confirmed in #1160): `damage`, `angle`,
`base_knockback`, `knockback_growth`, `set_knockback` (WDSK), circle size; and `set_id` (the
B-full hit-set registry, #888).

## Decision

Ruled field-by-field, human-gated, one field at a time.

### V1-in — schema carries the field AND the V1 DEV epic wires its engine seam

| Field | Stored representation | Engine seam |
|---|---|---|
| `hitlag_mult` (h) | `float = 1.0` (FOUND) | thread `h` into `hitlag_frames(damage, h)` — the per-hitbox term in `floor((d·0.3846154 + 5)·h·e)·c` |
| `shield_damage` | `int = 0` (FOUND) | `combat/shield.py` adds it to shield depletion (additive bonus beyond `damage`) |
| `ground` | `bool = True` (FOUND) | target-state gate in `systems/hit_resolution.py`: skip the hit if the defender is grounded and `ground` is false |
| `aerial` | `bool = True` (FOUND) | target-state gate: skip the hit if the defender is airborne and `aerial` is false |
| `hitbox_id` | `int` (FOUND; or the list-index-as-id convention) | change intra-move box selection from strongest-by-`max(damage)` (#130) to PM's lowest-`hitbox_id`-wins in `hit_resolution.py` |

Plus one **engine-seam-only** item that needs **no new stored field** (the value already rides
the stored `angle`):

- **angle sentinels 365 / 366 (autolink)** — add an attacker-motion-relative resolver beside the
  existing `knockback.sakurai_angle` (361, #203), so a move whose trajectory is 365/366 launches
  correctly instead of being mis-read as a literal ~365°.

### post-V1 — deferred; re-pulled from the live datamine when the engine grows to consume it

- `effect` (HitBoxEffect element) — electric branch + status-state subsystem both unbuilt; the
  hitlag `e` term stays fixed at 1.
- `sdi_mult` — no DI/SDI substrate at all (Phase 3).
- `can_be_shielded` / `can_be_reflected` / `can_be_absorbed` — no unshieldable moves authored;
  no reflector (Fox shine) / absorber (PSI Magnet) entities exist.
- `clank` (clang) + `direct` — clank needs a new resolver (overlap → 9%-priority-window →
  cancel/trade), not an additive field; `direct` only feeds clank + reflect/absorb.
- `angle_flipping` (AngleFlip enum) — per-variant launch-direction branching, not additive; the
  current facing-based launch matches the common variant.
- `sse_type` / `sound` / `sound_level` — cosmetic; no per-hit SFX/SSE system; `sse_type` is
  Brawl-specific and N/A to pycats.
- the also-present batch — `tripping_rate` (no trip mechanic), `flinchless`,
  `ignore_invincibility`, `freeze_frame_disable` (three real-but-niche cheap gates, kept out to
  keep V1 tight), `remain_grabbed`, `stretches_to_bone`, `can_hit1..13`, `enabled`
  (Brawl-engine bookkeeping).

### Unchanged

- `rehit_rate` — already consumed at the **move** level (`MoveData.rehit_rate`, #213). The
  datamine exposes it per-hitbox; pycats keeps it per-move. No per-hitbox schema change.

### The bar that governed the rulings

A field is V1-in when it is **cheap + its substrate already exists + it does real work**;
post-V1 when it **needs a new subsystem** or **completes nothing yet** (an inert store-ahead).
The additional signal: **completing or correcting an already-started engine seam** also counts
as V1-in even when it is not purely additive — this is why 365/366 (completing the angle-sentinel
seam) and `hitbox_id` (correcting the box-selection seam to PM's actual rule) are in, while
`clank`/`effect`/`angle_flipping` (net-new subsystems or branching) are out.

## Consequences

- **The V1-in stored set — `hitlag_mult`, `shield_damage`, `ground`, `aerial`, `hitbox_id` — is
  the concrete input to schema representation (#1150):** how these nest in the frozen `Hitbox`
  dataclass, serialize to `characters/data/<cat>.json`, and are read/written by the
  pycats-editor. The 365/366 resolver adds no field, so it does not touch #1150.
- **Fidelity gap — electric hitlag.** With `hitlag_mult` (h) in but `effect`/`e` deferred, an
  electric move's hitlag is computed without its ×1.5 multiplier. Accepted; re-pull `effect` and
  unfix `e` (and `c`) together in a later hitlag-terms pass.
- **Behaviour change — box selection.** Adopting lowest-`hitbox_id`-wins replaces the max-damage
  selection (#130). The downstream migration must re-verify every multi-box move (e.g. the
  Nalio/Mario jab, ids 0/1/2) and expect some render/sim goldens to shift — this is a real
  behaviour change, not a byte-identical refactor, so it lands with its own regression coverage.
- **Provenance.** The five V1-in stored values land as `FOUND` with datamine provenance, per the
  map's standing preference; most are at their inert default (h=1, shield_damage=0, ground/aerial
  true) until a move data-mines a non-default value.
- **No build here.** This ADR is a decision (the map is *plan, don't do*). The schema build, the
  five engine seams, the 365/366 resolver, and the all-move JSON migration are downstream DEV
  work, filed after the map clears.

## References

- ADR-0017 — store-what-the-engine-consumes principle (#1148), which this ADR's part (b) completes.
- #1160 findings — `docs/research/2026-08-03-datamine-per-hitbox-mechanics-engine-roles.md`.
- The map — datamined per-hitbox move data (#1147); next child is schema representation (#1150).
- KB/hitlag reference — `docs/pm-reference/combat-knockback-hitstun.md`; priority/clank —
  `docs/pm-reference/combat-hitboxes-priority.md`.
- Box selection #130; hit-set registry `set_id` #888; per-move `rehit_rate` #213; Sakurai
  sentinel `sakurai_angle` #203; invincibility `Tangibility.INVINCIBLE` #802.
