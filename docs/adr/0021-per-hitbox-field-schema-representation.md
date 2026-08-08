# ADR-0021 — per-hitbox field schema representation: where the ADR-0018 V1 fields live

- **Status:** Accepted  *(2026-08-04 — owner ruling on #1150, in a wayfinder grilling session)*
- **Date:** 2026-08-04

## Context

[ADR-0018](./0018-per-hitbox-field-v1-subset.md) (#1161) fixed **which** datamined per-hitbox
fields V1 stores — the V1-in set `hitlag_mult`, `shield_damage`, `ground`, `aerial`, `hitbox_id`
— on top of the [ADR-0017](./0017-store-what-the-engine-consumes-per-hitbox-field-principle.md)
store-what's-consumed principle. It did **not** fix the **representation**: how those fields nest
in the frozen `Hitbox` dataclass (`pycats/combat/data.py`), serialize into
`characters/data/<cat>.json`, and get read/written by the #792 editor. That is #1150, a
`wayfinder:grilling` child of the per-hitbox move-data map (#1147).

Two hard constraints bound the choice: the **frozen determinism boundary** (#768 — golden output
must not churn from an additive schema change) and the **JSON-flip regeneration seam** (#792 — the
editor round-trips `<cat>.json`). Precedent: `Hitbox` already grew `set_knockback` (#211),
`set_id` (#888), and `label` (#958) as flat, optional, defaulted scalars, and the loader
(`_select` → `_hitbox_from_json`) + omit-when-default serializer make such additions byte-identical
for existing data at zero loader cost.

## Decision

Ruled question-by-question, human-gated, in a grilling session on #1150.

### Q1 — overall shape: **flat scalars on `Hitbox`** (not a nested record)

The five V1-in fields are added as flat, optional, defaulted scalars — peers of the existing
`base_knockback`/`set_id`/`label` — not grouped under a nested `combat:` sub-record.

| Field | Representation | Default (= today's behaviour) |
|---|---|---|
| `hitlag_mult` | `float` | `1.0` |
| `shield_damage` | `int` | `0` |
| `ground` | `bool` | `True` |
| `aerial` | `bool` | `True` |
| `hitbox_id` | `int \| None` | `None` |

Rejected: a nested `CombatValues` sub-record (Option B) — it buys top-level tidiness but costs a
new `_combat_from_json` + serializer branch, a "fully-default → serialize to nothing" rule, and a
new editor sub-panel, for only five fields. Revisit B only if the post-V1 field batch (effect,
sdi_mult, can_be_*, clank/direct, angle_flipping, …) later lands and `Hitbox` genuinely bloats;
the flat→nested migration can happen then, with the full field set known.

### Q2 — `hitbox_id`: **its own int field**, not folded into `label`/`set_id`

`hitbox_id` is stored as the raw datamined id (`FOUND` provenance via the `StatusMap`), distinct
from the editor-authored `label` (A–Z identity letter) and the `set_id` hit-set tag. `label` is
authored and must not silently carry engine-selection meaning; the datamined id keeps its own
provenance. This refines ADR-0018's "`int` (or the list-index-as-id convention)" to
**`int | None = None`**, where `None` = today's behaviour (byte-identical) and a real id is
populated where datamined.

### Q3 — the `max(damage) → min(hitbox_id)` box-selection swap: **store now, consume later**

#1150 lands `hitbox_id` as **stored-but-unread** data. The behaviour-changing selection swap
(ADR-0018 flags it as golden-churning) is deferred to its **own DEV** (#1214, blocked by the
schema-build #1213), which ships it with a revert-check regression test and a reviewed golden
regeneration. This keeps the entire #1150 representation slice byte-identical, honouring the frozen
boundary; the consumer is filed and sequenced, not hypothetical.

### Q4 — `ground` / `aerial`: **two bools**, not one enum

Modelled as two independent booleans (`ground: bool = True`, `aerial: bool = True`), mirroring the
datamine's two flags 1:1 (cite-primary discipline) and defaulting both `True` = "hits both" =
today. A 3-value enum `{GROUND, AERIAL, BOTH}` would re-encode two source flags into one and cannot
represent the degenerate "hits neither" state that two bools express naturally.

### Q5 — golden safety: **omit-when-default**, `schema_version` stays `1`

The additions are backward-compatible by construction: an existing `<cat>.json` missing the keys is
indistinguishable from a new doc that left them at default, so old data hydrates to the defaults
unchanged and the serializer omits each field at its default → every existing file and golden stays
byte-identical. No `schema_version` bump (which would force a no-op rewrite of every fighter file
and, given the loader's exact-match guard, cannot be done incrementally). Reserve a version bump
for a genuinely breaking reshape (e.g. if Option B's nested record is ever adopted).

## Consequences

- The `Hitbox` frozen dataclass widens toward ~15 fields; KB physics, hit-set identity, and
  interaction-gating all live flat in one namespace — accepted as the cost of the zero-migration,
  golden-safe path.
- Each datamined value rides the existing per-field `StatusMap` (#1133) for `FOUND` provenance; the
  representation choice does not disturb that map.
- The #792 editor must **round-trip-preserve** all five fields on save (authoring UI may be
  deferred; passthrough preservation cannot).

## Downstream (filed after this ruling)

- **#1213** — DEV: add the five fields to the `Hitbox` schema + serialization + editor round-trip
  (representation only, byte-identical). The direct executor of this ADR.
- **#1214** — DEV: the `max(damage) → min(hitbox_id)` box-selection swap (Q3), **blocked by #1213**;
  reconcile with #829 (same-frame multi-box resolution research) before implementing.
- **Not yet filed (downstream of #1147's engine-consumption seam design):** wiring the remaining
  consumers — `hitlag_mult` → `hitlag_frames`, `shield_damage` → `shield.py`, `ground`/`aerial` →
  `hit_resolution` target-state gate. Filed one at a time per the #1147 discipline.

## References

#1150 (this ruling) · #1147 (per-hitbox move-data wayfinder map) · ADR-0018 (#1161, V1 field
subset) · ADR-0017 (#1148, store-what's-consumed) · #1117 (author-boxes epic) · #768 (frozen
determinism boundary) · #792 (editor / JSON-flip seam) · #1133 (per-field status map) ·
#211/#888/#958 (the `set_knockback`/`set_id`/`label` additive-scalar precedent) ·
#829 (same-frame multi-box resolution research).
