# Datamine per-hitbox mechanics & their pycats engine roles

**Ticket:** investigate datamine per-hitbox mechanics and their engine roles (#1160,
`wayfinder:research`, child of the datamined per-hitbox move data map #1147).
**Governing principle:** store-what's-consumed (ADR-0017, from #1148).
**Date:** 2026-08-03 · **Agent:** cherry.

This is a **research findings doc only** — no inclusion decision. Which of these fields
become V1 schema fields vs post-V1 is the sibling architect ticket #1161.

## What this covers

For every datamined per-hitbox field that pycats does **not** already store+consume, this
records: (1) the real mechanic with a primary quote, (2) whether the pycats engine consumes
it today (code path, or "absent"), and (3) what would have to exist for it to be consumed.

**Already stored + consumed — out of scope (confirmed):** `damage`, `angle`,
`base_knockback` (BKB), `knockback_growth` (KBG), `set_knockback` (WDSK), circle `size`.
Verified in `pycats/systems/hit_resolution.py` — the hit-apply block reads exactly these off
the resolved `Hitbox` (`atk.damage = hit_box.damage`, `…angle`, `…base_knockback`,
`…knockback_growth`, `…set_knockback` / WDSK #211) and feeds `knockback()` /
`set_knockback()` in `pycats/combat/knockback.py`.

## Primary sources

- **The datamine field set (authoritative):** `brawllib_rs/src/high_level_fighter.rs`,
  `struct HitBoxValues` — the full per-hitbox field list the `high_level_frame_data`
  renderer exposes. Enums in `brawllib_rs/src/script_ast/mod.rs` (`HitBoxEffect`,
  `AngleFlip`, `HitBoxSound`, `HitBoxSseType`).
- **The KB/hitlag/hitstun pipeline:** `docs/pm-reference/combat-knockback-hitstun.md`.
- **Priority/clank:** `docs/pm-reference/combat-hitboxes-priority.md`.
- **Engine source:** `pycats/combat/` (`knockback.py`, `shield.py`, `data.py`,
  `move_clock.py`) + `pycats/systems/hit_resolution.py` + `pycats/entities/attack.py`.

`HitBoxValues` (verbatim field list, `brawllib_rs/src/high_level_fighter.rs`):

```
hitbox_id, set_id, damage, trajectory, wdsk, kbg, shield_damage, bkb, size,
tripping_rate, hitlag_mult, sdi_mult, effect, sound_level, sound, ground, aerial,
sse_type, clang, direct, rehit_rate, angle_flipping, stretches_to_bone,
can_hit1..can_hit13, enabled, can_be_shielded, can_be_reflected, can_be_absorbed,
remain_grabbed, ignore_invincibility, freeze_frame_disable, flinchless
```

## The `pycats` Hitbox today

`pycats/combat/data.py` `Hitbox` (frozen) carries: `circle`, `damage`, `angle`,
`base_knockback`, `knockback_growth`, `active_start`, `active_end`, `set_knockback` (WDSK),
`set_id`, `label`, `status`. Everything below is **not a field on `Hitbox`** unless stated.

---

## Field-by-field findings

### effect (`HitBoxEffect`)

- **Mechanic.** A 24-variant element enum (`brawllib_rs/src/script_ast/mod.rs`
  `pub enum HitBoxEffect`): `Normal, None, Slash, Electric, Freezing, Flame, Coin, Reverse,
  Trip, Sleep, Bury, Stun, Flower, Grass, Water, Darkness, Paralyze, Aura, Plunge, Down,
  Flinchless`. Two kinds of coupling: (a) **engine** — `Electric` multiplies hitlag by 1.5
  (the `e` term: *"`e` electric multiplier (1.5× if electric, else 1)"*,
  `combat-knockback-hitstun.md`); several variants (`Freezing`, `Bury`, `Sleep`, `Stun`,
  `Flower`, `Paralyze`, `Trip`) impose their own victim status states; (b) **cosmetic** —
  hit spark colour / sound family.
- **pycats today: absent.** No `effect` field on `Hitbox`. `hitlag_frames(damage)`
  (`knockback.py`) hard-codes `e = 1` — its docstring: *"The per-move (h), electric (e) and
  crouch-cancel (c) multipliers are 1 in this slice (#138)."* The reference doc's
  implementation-status list confirms: *"Hitlag `h`/`e`/`c` multipliers … fixed at 1"*
  (#135). No status-effect state machine exists (no freeze/bury/sleep). `effect` is **not**
  in `docs/glossary.md`.
- **To consume.** Minimum (electric only): add an `effect`/`is_electric` field, branch
  `e = 1.5` in `hitlag_frames`. Full: a status-effect subsystem (freeze/bury/sleep/… each a
  new victim state) — a large downstream feature, not a field plumb.

### hitlag_mult (`h`)

- **Mechanic.** The per-hitbox hitlag multiplier `h` (default 1) in
  `hitlag = floor((d · 0.3846154 + 5) · h · e) · c` (`combat-knockback-hitstun.md`;
  datamine `hitlag_mult: f32`). Lets a specific hit freeze longer/shorter than its damage
  implies.
- **pycats today: absent.** Not stored; `hitlag_frames` fixes `h = 1` (#135, #138, same
  code path as `effect`/`e`).
- **To consume.** Add the field; thread `h` into `hitlag_frames` (which currently takes only
  `damage`). Self-contained — no new subsystem, unlike `effect`'s status states.

### sdi_mult

- **Mechanic.** Per-hitbox SDI (Smash Directional Influence) multiplier (datamine
  `sdi_mult: f32`) scaling how far rapid stick inputs *during hitlag* nudge the victim.
- **pycats today: absent, and no substrate.** pycats models **no DI or SDI at all**:
  *"**DI / SDI** — not implemented (Phase 3)"* (`combat-knockback-hitstun.md`
  implementation-status list). Nothing reads stick input during hitlag.
- **To consume.** Requires the whole DI/SDI input-during-hitlag system first; `sdi_mult` is
  a tuning knob on a mechanic that does not yet exist. Far downstream.

### shield_damage + can_be_{shielded, reflected, absorbed}

- **Mechanic.** `shield_damage: i16` = extra shield depletion a hit deals beyond its damage;
  `can_be_shielded / can_be_reflected / can_be_absorbed: bool` gate whether a shield /
  reflector (Fox shine) / absorber (Ness PSI Magnet) interacts with the hit.
- **pycats today: shields exist, these fields do not.** `pycats/combat/shield.py` models
  `shieldstun_frames(damage)` and `shield_break_stun_frames(percent)` — but shieldstun is
  computed from the hit's **regular `damage`**, not from a separate `shield_damage` value,
  and `grep` finds no `shield_damage`, `can_be_shielded`, `reflect`, or `absorb` anywhere in
  `pycats/`. There is no reflector or absorber entity.
- **To consume.** `shield_damage`: `shield.py` reads a per-hitbox shield-damage bonus into
  shield depletion (small, additive). `can_be_reflected`/`can_be_absorbed`: need
  reflector/absorber mechanics + entities that do not exist (large). `can_be_shielded`:
  today every hit is implicitly shieldable; a gate is trivial once a field exists but changes
  little until unshieldable moves are authored.

### clang (clank) + direct

- **Mechanic.** `clang: bool` — does this hitbox participate in **clank**, the deterministic
  move-vs-move priority contest: *"purely from the two attacks' damage, using the 9%
  'priority range' … Aerials do not clank"* (`combat-hitboxes-priority.md`). `direct: bool`
  distinguishes a **direct** hit (the fighter's own hitbox) from an **indirect** one
  (a detached projectile/item), which matters for clank and for reflect/absorb eligibility.
- **pycats today: documented, not implemented.** No clank code exists (`grep clank|clang` in
  `pycats/` is empty). The one artifact is anticipatory: `AttackHitbox.in_air` (#133) carries
  the comment *"is this an aerial move's hitbox? (aerials don't clank)"* and is plumbed
  through (`move_clock.py`, `player.py`) but **no code reads it to resolve priority** — there
  is nothing to gate yet. `direct` is not modelled.
- **To consume.** Implement clank: when two opposing active hitboxes overlap, compare damage
  against the 9% window and cancel/trade; gate with the already-plumbed `in_air` (aerials
  skip) and a stored `clang`/`direct`. Note pycats' `in_air` is the **attacker's** move-is-
  aerial flag, distinct from the datamine `ground`/`aerial` **target** flags below.

### angle_flipping + angle sentinels (361 / 365 / 366)

- **Mechanic.** Two separate things. (a) `angle_flipping` (`AngleFlip` enum,
  `script_ast/mod.rs`): how the launch direction is chosen —
  `AttackerPosition, MovementDir, LeftDir, AttackerDir, AttackerDirReverse, HitboxPosition,
  FaceZaxis`. (b) **Angle sentinels** — special `trajectory` values resolved at hit time:
  *"361 — the Sakurai angle"* (airborne fixed, grounded scales flat→up with KB) and
  *"365 / 366 — autolink angles"* that scale with the attacker's own motion
  (`combat-knockback-hitstun.md`).
- **pycats today: partial.** The **361 Sakurai** sentinel **is** resolved —
  `knockback.sakurai_angle(kb, on_ground)` (#203), consumed in the launch path. **`angle_flipping`
  is absent** (no field; launch direction is derived simply from attacker facing) and the
  **365/366 autolink** sentinels are **documented but not implemented** (no handler; `grep
  angle_flip` empty).
- **To consume.** `angle_flipping`: add the field + apply the chosen flip rule at launch-
  direction resolution (small, but touches a subtle correctness area). Autolink 365/366:
  add attacker-motion-relative angle resolution alongside the existing `sakurai_angle`.
  The `SAKURAI_*` constants are flagged *"unsourced ⚠ playtest starting points, not exact PM
  values"* — orthogonal, but worth noting the existing sentinel path is not yet cited.

### ground / aerial (target-state flags)

- **Mechanic.** `ground: bool` / `aerial: bool` on the hitbox = **which victim states this
  box can connect with** (can-hit-grounded / can-hit-airborne). A box with `aerial=false`
  whiffs an airborne target.
- **pycats today: absent.** Not stored, not consumed — every active hitbox can hit any
  target regardless of the defender's grounded/airborne state (`hit_resolution.py` does no
  such gating). **Do not confuse** with pycats `in_air` (the *attacker's* move-is-aerial flag
  for clank) — that is a different axis.
- **To consume.** `hit_resolution.py` checks the defender's `on_ground` against the box's
  `ground`/`aerial` flags before registering the hit. Small, localized.

### hitbox_id vs pycats `label` / `set_id`

- **Mechanic.** `hitbox_id: u8` — **intra-move priority**: *"Hitbox-id priority decides which
  one. When several of a move's hitboxes overlap the target, the one with the highest
  priority (lowest hitbox id) [connects]"* (`combat-hitboxes-priority.md`). `set_id: u8` —
  the **hit-set group**: boxes sharing a `set_id` share one connect-registry (multi-hitbox,
  single-connect).
- **pycats today: mixed.** `set_id` **is** stored on `Hitbox` **and consumed** — the B-full
  per-move-instance hit-set registry (#888): boxes sharing a `set_id` consult a shared
  target list (`hit_resolution.py`, `move_clock.py`, `player.py::_hit_sets`) so a
  multi-box move connects once. pycats `label` is an **editor display letter** (#1036), not
  from the datamine. **`hitbox_id` (priority) is NOT stored** — and pycats resolves
  multi-box overlap differently: it picks the **strongest box by max damage** (#130,
  `hit_resolution.py`: *"strongest box … `max(hb.damage for hb in boxes)`"*), **not** the
  lowest-id box. That is a **fidelity gap** vs PM's id-priority rule.
- **To consume `hitbox_id`.** Store it and change the strongest-box selection from
  max-damage to lowest-`hitbox_id`. Behaviour-changing (could alter which box's angle/KB
  applies on overlap) — flag for careful review if included.

### sse_type + sound (+ sound_level)

- **Mechanic.** `sse_type: HitBoxSseType` (Subspace-Emissary interaction type),
  `sound: HitBoxSound` (hit-SFX family: `Punch, Kick, Slash, …`), `sound_level: u8`
  (loudness). Audio / cosmetic.
- **pycats today: absent.** Not stored, not consumed; pycats has no per-hitbox SFX or SSE.
  **Display/audio-only** — confirmed lowest-relevance.
- **To consume.** Requires a hit-sound system; purely cosmetic, no engine coupling. Lowest
  priority of the set.

---

## Also-present datamine fields (not in the ticket list)

`HitBoxValues` carries more per-hitbox fields the ticket didn't enumerate; recording their
status so #1161 has the full picture:

- **rehit_rate** — **already consumed**, but at the **move** level, not per-hitbox:
  `MoveData.rehit_rate` drives looping multi-hit (#213, `entities/attack.py`
  `_rehit_timer`). The datamine exposes it per-hitbox; pycats stores it per-move.
- **tripping_rate** — chance a hit trips instead of launches. Absent; no trip mechanic.
- **flinchless** — the hit deals damage but no hitstun/flinch. Absent.
- **ignore_invincibility** — bypasses the defender's invincible state (cf. pycats
  `Tangibility.INVINCIBLE`, #802). Absent; would interact with `combat/tangibility.py`.
- **freeze_frame_disable** — suppresses this hit's hitlag. Absent.
- **remain_grabbed**, **stretches_to_bone**, **can_hit1..can_hit13**, **enabled** —
  Brawl-engine bookkeeping (grab retention, stretched hitbox interpolation, hit-group
  bitmask, box on/off). Not pycats concepts today.

## Summary table

| Datamine field | Mechanic | pycats consumes today? | Cost to consume |
|---|---|---|---|
| `effect` | element; Electric→hitlag×1.5 + status states | No (`e` fixed 1, #135) | electric: small · status effects: large subsystem |
| `hitlag_mult` (`h`) | per-hit hitlag scale | No (`h` fixed 1, #135) | small (thread `h`) |
| `sdi_mult` | SDI scaling | No — no DI/SDI at all (Phase 3) | large (needs SDI system) |
| `shield_damage` | extra shield depletion | No (shieldstun uses `damage`) | small (additive) |
| `can_be_{shielded,reflected,absorbed}` | shield/reflect/absorb gates | No | reflect/absorb: large; shield gate: small |
| `clang` (clank) + `direct` | move-vs-move priority; direct/indirect | No — documented, `in_air` plumbed but unread | medium (clank resolution) |
| `angle_flipping` | launch-direction flip rule | No | small |
| angle sentinels 361 / 365,366 | Sakurai / autolink | **361 yes** (`sakurai_angle` #203); 365/366 no | 361 done · autolink small–medium |
| `ground` / `aerial` (target) | can-hit-grounded/airborne gate | No | small (localized) |
| `hitbox_id` | intra-move priority (lowest-id wins) | No — pycats uses **max-damage** (#130) | medium (behaviour-changing) |
| `set_id` | hit-set group | **Yes** — B-full registry (#888) | (already consumed) |
| `sse_type` / `sound` | audio / SSE | No | cosmetic (needs SFX system) |

## Handoff

Feeds the per-field V1 vs post-V1 inclusion decision (#1161), which turns each row above into
a V1-in (stored + engine-seam noted) or post-V1-out ruling. No inclusion decision is made
here. Evidence quality is Avi's call: the datamine field set and the engine-consumption
status are primary-sourced (struct + code paths quoted); the "cost to consume" column is
inference/estimate, not a commitment.
