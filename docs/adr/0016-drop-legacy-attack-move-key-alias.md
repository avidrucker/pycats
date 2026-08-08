# ADR-0016 — drop the legacy `attack` move-key alias

- **Status:** Accepted  *(2026-08-03 — owner ruling on #1155, in a wayfinder grilling session)*
- **Date:** 2026-08-03

## Context

pycats character move data (`characters/data/<cat>.json`, hydrated into `FighterData` in
`combat/data.py`) carried a legacy `"attack"` **move-data key** that meant different things per
cat, and `combat/move_select.py::resolve_move_key` used `"attack"` as a generic fallback whenever
a requested move slot was undefined. The #1149 mapping audit
(`docs/research/2026-08-02-move-subaction-mapping-audit.md`) surfaced the ambiguity:

- **nalio & birky** have **no** `dtilt` key — their `"attack"` key *is* the down-tilt
  (`attack.name` = "down tilt" / "dtilt", 3 hitboxes, mapped to `AttackLw3`).
- **narz & gnok** have a real `dtilt` key *plus* a dead 1-hitbox `"attack"` leftover
  (`attack.name` = "attack", left unmapped in the gif_map — the two "intentional non-maps").
- **default/testcat** has **only** an `"attack"` key (`name:"attack"`, ground, 1 hitbox, 3/3/6).
  It is reachable in production: `load_fighter_data` hydrates `default.json` for the
  intended-default seats `{"default","P1","P2","testcat"}`, and unknown/None selections fold into
  `testcat` before the seam (#672/#894). So its kit matters at runtime, and the `move_select`
  `"attack"` fallback is reachable through it.

The string `"attack"` is also the **input action** (the A button — `controls["attack"]`,
`input_script.ACTIONS`, `keymap`). That is a separate concern that shares a spelling; it is **not**
touched by this decision.

The goal: only named moves live in the character JSON and the pycats-editor — no ambiguous
`"attack"` move-data key, and no hidden fallback resolving to it.

## Decision

### Partial-kit contract — no fallback

`resolve_move_key` gets **no** generic fallback. When a cat does not define a requested move slot,
**no move fires** (the input is dropped) — there are no hidden defaults. All three current fallback
branches are removed:

- ground-A without the specific tilt/jab key,
- air-A without a `nair`,
- smash without the corresponding tilt.

The four playable cats (nalio, birky, narz, gnok) ship full kits, so only the default/testcat
fixture is affected by the no-op behavior on undefined slots.

### Per-cat migration

| cat | action | rationale |
|-----|--------|-----------|
| **nalio** | rename `attack` → `dtilt` | `attack` **is** its down-tilt; pure key rename, no data lost |
| **birky** | rename `attack` → `dtilt` | same as nalio |
| **narz** | **delete** `attack` | dead 1-hitbox cruft beside a real `dtilt`; unreachable once the fallback is gone |
| **gnok** | **delete** `attack` | same as narz |
| **default/testcat** | rename `attack` → `jab` | keeps one usable neutral move under a clean named key; every other slot no-ops |

**Invariant:** every cat defines `jab`; nothing resolves to `attack` anywhere.

### Editor

The pycats-editor offers **named moves only** — `"attack"` is removed from its move-key
vocabulary, and there is **no** legacy read-compat path (after this migration no shipped JSON
carries `attack`). Implemented as a downstream editor DEV ticket in the pycats-editor repo.

### Input action untouched

The input action `"attack"` (the A button) is left exactly as-is. Only the move-*data* key is
removed; the two merely share a spelling.

## Consequences

- **`move_select.py`** loses its `"attack"` fallback branches; `resolve_move_key` returns
  "no move" for an undefined slot rather than aliasing to `attack`.
- **Regression tests (able-to-fail, per repo rule):** nalio/birky down-tilt must still fire — now
  under `dtilt`; nothing resolves to `attack`; the default/testcat cat no-ops on undefined slots
  and still throws its `jab`.
- **Blast radius (downstream DEV, not this ADR):** ~10+ tests use `moves["attack"]` as a fixture,
  and `test_move_select.py` asserts the old fallback (`… == "attack"`). These flip to `dtilt` /
  `jab` per cat, and the fallback assertion is rewritten to assert "no move."
- **Long-term (follow-up, out of this ADR's scope):** the default/testcat cat is slated to be
  either deleted outright or rebuilt from scratch; this ADR only renames its one move so the
  cleanup can land now without inventing fixture data.

## Downstream tickets (filed after the wayfinder map #1147 clears)

- **pycats migration DEV** — the four JSON renames/deletes + `default.json` rename + drop the
  `move_select` fallbacks + fix the affected tests, with the regression tests above.
- **pycats-editor DEV** — remove `attack` from the editor vocabulary (separate repo).

## References

- Map: datamined per-hitbox move data — wayfinder map (#1147).
- Ruling ticket: #1155.
- Grounding: #1149 mapping audit (`docs/research/2026-08-02-move-subaction-mapping-audit.md`),
  `combat/move_select.py`, `combat/data.py::load_fighter_data`,
  `characters/data/{nalio,birky,narz,gnok,default}.json`.
