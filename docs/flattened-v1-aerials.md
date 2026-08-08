# V1-flattened lingering aerials

**Restore breadcrumb for the post-V1 sex-kick / juggle mechanic.**

V1 has no lingering-aerial (sex-kick) mechanic (ruling #893, tracked #911). Five
two-window aerials each carried a strong early "clean" hitbox overwritten by a
weaker "late" one; under the #204 per-window model each spawned a separate Attack
per window, so a stationary target was double-hit (#879/#890 Facet 3). The #893
game-designer ruling **flattens** each to ONE window over the full active span,
with placeholder values = the average of the old clean+late numeric fields (angle
kept from the clean window where the two differed — never averaging the Sakurai
sentinel 361). The mechanic is restored post-V1 on top of #888 (B-full).

These placeholder numbers are marked
`human-designer-temporary-placeholder-values-for-v1-only` — **no parity claim**.

Until #1141 this breadcrumb lived as source comments in the Python oracle
(`nalio_cat.py`, `birky_cat.py`). #1141 retired those oracles (the shipped
`characters/data/<cat>.json` mirror is the sole source, which carries no
comments), so the greppable list moved here. `tests/test_flatten_lingering_aerials.py`
asserts this doc still lists every flattened move; the flattened *values* are
pinned by that test's `CASES` table against the shipped JSON.

## The flattened moves

| Move | Windows before | Flattened window | Boxes |
| --- | --- | --- | --- |
| `nalio.bair` | clean + late | one, full active span | 2 |
| `nalio.uair` | clean + late | one, full active span | 2 |
| `birky.nair` | clean + late | one, full active span | 1 |
| `birky.bair` | clean + late | one, full active span | 2 |
| `birky.uair` | clean + late | one, full active span | 2 |

## Post-V1 restore

A restore ticket (downstream of #888 B-full) reinstates the clean/late two-window
form for each move above, replacing the `-v1-only` placeholder numbers with
sourced values. Grep this file (or the marker token) to find the full set.
