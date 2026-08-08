# ADR-0017 — per-hitbox field set: store what the engine consumes

- **Status:** Accepted  *(2026-08-03 — owner ruling on #1148, in a wayfinder grilling session)*
- **Date:** 2026-08-03

## Context

The datamined per-hitbox move data map (#1147) needs to decide **which** of the
`high_level_frame_data` per-hitbox fields the pycats move schema carries, and **which** the
combat/knockback engine consumes (the two subsets may differ — some datamined fields are
display / audio only). #1148 was the root ticket for that question.

Grounding facts established during the grilling:

- **The core KB inputs are already stored and already consumed.** `Hitbox` (`combat/data.py`)
  already carries `damage`, `angle`, `base_knockback` (BKB), `knockback_growth` (KBG),
  `set_knockback` (WDSK), and the circle size — and the KB formula in
  `docs/pm-reference/combat-knockback-hitstun.md` consumes exactly those (plus the defender's
  weight, which is a fighter attribute, not per-hitbox). So the root question is really about the
  **remaining** datamine fields: effect, hitlag_mult, sdi_mult, shield_damage +
  can_be_{shielded,reflected,absorbed}, clank, direct, angle_flipping, ground/aerial, hitbox_id,
  sse_type, sound.
- **Stored fields are real surface area.** Each field on the frozen dataclass is carried through
  the determinism boundary (#768), the JSON serializer, every render/sim golden, the
  pycats-editor, and the provenance registry. A stored field that nothing reads can drift stale
  with no test exercising its value to catch it.
- **The datamine is live and repeatable.** The `brawllib_rs` `high_level_frame_data` environment
  is set up and re-runnable, so re-pulling a field later — when the engine grows to consume it —
  is cheap.

## Decision

**Governing principle (A): store only what the engine consumes, plus what the editor must
display.** A datamined per-hitbox field is added to the pycats schema only when there is an
engine seam that reads it (or the editor must show it); fields that nothing consumes yet are
**deferred (post-V1)** and re-pulled from the live datamine when the engine grows to need them.

Rejected alternative **(B): store the full datamine record faithfully (superset)** — capture
provenance once for every field even if inert. Declined because it carries un-exercised fields
through the frozen boundary, the editor, and every golden, where they can drift with nothing
reading them; the repeatable datamine makes deferral low-cost, so the provenance-capture-once
benefit does not outweigh the surface-area cost.

### Decomposition (part (b) delegated)

This ADR fixes the **principle**. The concrete per-field subset (#1148 part (b) — the exact
stored subset and engine-consumed subset) is delegated to two sibling tickets under the map
#1147:

- **#1160** (`wayfinder:research`) — establish each remaining field's real mechanic and its
  actual engine role (or confirm it has none yet), grounded in the datamine + KB/hitlag/hitstun
  docs + engine source. Findings doc, no inclusion decision.
- **#1161** (`wayfinder:grilling`, role ARC, **blocked by #1160**) — decide field-by-field which
  mechanics are **V1** (in the schema, with saved values) vs **post-V1** (deferred), applying
  this (A) principle. Its V1-in set is the concrete stored + consumed subset, and it feeds schema
  representation (#1150, re-pointed to block on #1161).

## Consequences

- The default posture for any not-yet-consumed datamined field is **out** of the V1 schema until
  #1161 rules it in against a real engine seam.
- Schema representation (#1150) blocks on #1161, not on #1148 — the fields to represent come from
  the per-field ruling, not from this principle alone.
- Fields deferred post-V1 are not lost: the datamine env is repeatable, so a later engine feature
  re-pulls them with `FOUND` provenance at that time.

## References

- Map: datamined per-hitbox move data — wayfinder map (#1147).
- Ruling ticket: #1148. Siblings spawned: #1160 (research), #1161 (per-field decision).
- Grounding: `combat/data.py::Hitbox`, `docs/pm-reference/combat-knockback-hitstun.md`,
  the live `high_level_frame_data` datamine.
