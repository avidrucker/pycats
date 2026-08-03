# Authored-vs-sourced value ratchet — design findings (#1125)

**Role:** RESEARCH (design). **Sequenced after** #1124 (the authored-vs-sourced audit) and
#1129/#1133 (the per-fighter value-status seam). This doc **consumes** the seam decided in
#1129 and built in #1133 — it does **not** re-open the "where does status live" question.

This is a findings + design doc. It lays out the counter + ratchet design and an option space
for the genuinely-open questions, each with a recommendation. **It does not build anything** —
the build is a follow-on DEV ticket.

> **Ratified 2026-08-02** (guide-human-decision session, Avi ruling). The four design questions
> in §6 were decided live; each carries its ruling inline below, and §9 sketches the follow-on
> DEV ticket the rulings authorize. The option analysis is retained for traceability.
>
> | # | Decision | Ruling |
> |---|---|---|
> | Q1 | Census home | **Separate `combat/value_status_census.py` reader** over both loci |
> | Q2 | Undeclared values | **UNDECLARED bucket + ratchet it** (may only drop) |
> | Q3 | v1 gate scope | **Authored + undeclared only** — FOUND-drop guard NOT in v1 |
> | Q4 | Baseline home | **Per-area `tests/authored_value_baseline.json` + `PYCATS_UPDATE_AUTHORED_BASELINE=1` re-bless** |

---

## 1. What the ratchet is for

Value status is now machine-readable in two places, but nothing *counts* it or *guards the count
over time*. A guessed/placeholder number can be added to a fighter or a config scalar and no test
notices. The ask (#1125): a **runnable counter** of `{authored, sourced, derived}` per area, plus
a **ratchet regression** that reds when the *authored* count grows without a deliberate baseline
bump — so guesses can't accumulate without visibility. The count must be free to **drop** (a value
gets sourced/TUNED), and a drop is progress.

---

## 2. The two status loci this counter reads

| Locus | What it covers | Shape | Status vocabulary |
|---|---|---|---|
| `combat/provenance.py` → `TUNING_PROVENANCE` | sourced combat/physics **scalars** in `config.py` | typed `Provenance` rows keyed by config attr name; `status` is a plain string | FOUND · GUESS · TUNED · DIVERGENCE (4) |
| the #1133 seam (`combat/data.py`) → `status: StatusMap` on `Circle`/`Hitbox`/`MoveData`/`VelocityPhase`/`LandingSpawn`, serialized into `characters/data/*.json` | per-fighter **move data** (damage, angles, knockback, radii, offsets, recovery velocities) | `FieldStatus(status: Status, source)` keyed by field name | FOUND · GUESS · TUNED · DIVERGENCE · **PLACEHOLDER** (5) |

The vocabularies are **almost** the same. The fighter seam adds `PLACEHOLDER` (a stand-in where no
real value exists yet); `provenance.py`'s string status has no PLACEHOLDER by construction. A
unified counter must handle the **union of 5 statuses** and accept that PLACEHOLDER is simply
absent from the config-scalar side.

CPU controller constants are **out** (#1129 Q4, ruling #704) — they are not in either registry.

### Status → bucket mapping (the crux)

| Bucket | Statuses | Meaning | Ratcheted? |
|---|---|---|---|
| **authored** | `GUESS` + `PLACEHOLDER` | not-canon, not a deliberate design value — a debt to source or fill | **yes — reds on growth** |
| **sourced** | `FOUND` | traced to a cited canon value | reported |
| **decided** | `TUNED` + `DIVERGENCE` | deliberate design value / intentional departure — not seeking canon | reported |

**Count `PLACEHOLDER` apart from `GUESS` inside the authored bucket** (#1129 vocabulary rationale):
they are different debts — PLACEHOLDER is a *hole to fill* (no real number yet), GUESS is a *real
number to source* (a playtest starting point). Progress on each should be independently visible, so
the counter carries both as sub-tallies under `authored`, not a merged total.

---

## 3. Current baseline snapshot (as of 2026-08-02, this branch)

Real counts, so the follow-on build starts from a known number:

**`provenance.py` (60 scalar rows):**

| Bucket | Count | Detail |
|---|---|---|
| authored | **11** | GUESS 11 · PLACEHOLDER 0 |
| sourced | 25 | FOUND 25 |
| decided | 32 | TUNED 25 · DIVERGENCE 7 |

**Fighter seam (`characters/data/*.json`):**

| Fighter | authored | sourced | decided | declared total |
|---|---|---|---|---|
| birky | 15 (PLACEHOLDER 15) | 21 (FOUND) | 0 | 36 |
| nalio | 0 | 0 | 0 | **0 — undeclared** |
| narz | 0 | 0 | 0 | **0 — undeclared** |
| gnok | 0 | 0 | 0 | **0 — undeclared** |
| default | 0 | 0 | 0 | **0 — undeclared** |

Only **birky** carries declared status today (it was the #1133 exemplar). The other four fighters'
move values are real, authored, and **invisible to any declared-status counter** — see §5, the
central design decision.

---

## 4. The counter (runnable, per-area)

A reader that enumerates both loci and returns per-area buckets. Suggested home: a new thin
module `combat/value_status_census.py` that *imports and reads* both registries — it does **not**
merge them (see §6 Q1). Sketch of its return shape:

```python
# census() -> dict[area, Buckets]
{
  "physics_config": {"authored": {"guess": 11, "placeholder": 0}, "sourced": 25, "decided": 32},
  "fighter:birky":  {"authored": {"guess": 0,  "placeholder": 15}, "sourced": 21, "decided": 0},
  "fighter:nalio":  {"authored": {...}, "sourced": ..., "decided": ..., "undeclared": <N>},
  ...
  "TOTAL":          {"authored": {...}, "sourced": ..., "decided": ..., "undeclared": ...},
}
```

- **physics_config** area: iterate `TUNING_PROVENANCE.values()`, tally by `status`.
- **fighter:<stem>** areas: `load_fighter_data(stem)` (the R8 hydrate path), walk each
  `Hitbox`/`Circle`/`MoveData`/`VelocityPhase`/`LandingSpawn`, tally each `FieldStatus.status`
  in its `status` map; the *undeclared* count is the design decision in §5.
- Expose it two ways: an importable `census()` for the ratchet test, and a `__main__` / Make
  target that prints the table for a human (mirrors how `provenance` is human-readable).

The counter is pure/read-only and headless — it fits the existing test harness with no pygame.

---

## 5. The central decision: undeclared values

The counter only sees **declared** statuses. 4 of 5 fighters carry zero. Their authored values are
exactly the "guesses accumulating invisibly" the ratchet exists to stop — and a declared-only
counter would report them as *nothing at all*, the worst outcome. Three ways to handle it:

| Option | Behavior | Cost | Serves the intent? |
|---|---|---|---|
| **(a) Coverage gate** | a separate test asserts *every* value carries a status; no value may be undeclared | large upfront annotation pass across 4 fighters + all scalars before the ratchet is meaningful | fully, but blocks on a big prerequisite |
| **(b) UNDECLARED bucket + ratchet** ⭐ | count values with no status as their own bucket; ratchet it too (undeclared may only drop) | needs a per-fighter "total value slots" enumeration so undeclared = slots − declared | yes — makes the invisible visible without a full annotation pass first |
| **(c) Declared-only** | ignore undeclared entirely | none | **no — defeats the purpose**; an undeclared guess is invisible |

**Recommendation: (b). → RATIFIED 2026-08-02.** It directly serves "guesses can't accumulate
invisibly" without blocking on a full annotation sweep, and it converges toward (a) naturally: as
fighters get annotated, undeclared drops to zero and the coverage gate becomes a cheap follow-on.
(c) is a non-starter for this ticket's stated goal. The coverage gate (a) is a **separate later
ticket**, not bundled.

Note (b) requires the counter to know the **denominator** — how many value-slots a fighter *has* —
to compute undeclared. That enumeration (walk the dataclass fields that are eligible for a status)
is the one piece of new machinery beyond "tally the maps."

---

## 6. Design questions → options, recommendations, and rulings

*All four ratified 2026-08-02 (see banner at top). Rulings inline as **→ RATIFIED**.*

### Q1 — Extend `provenance.py`, or a separate census seam? → RATIFIED: separate reader
- **Recommendation: separate reader**, `combat/value_status_census.py`, composed over both loci.
  The two registries have different shapes (typed `Provenance` rows vs `StatusMap` on frozen
  dataclasses) and different scopes (config scalars vs per-fighter move data). Folding them into one
  registry re-braids two independent concerns; a census that *reads* both keeps them apart
  (composition, not merge). `provenance.py` stays the config-scalar SSOT; the #1133 seam stays the
  fighter SSOT.

### Q2 — Where does the baseline live, and how is a bump reviewed? → RATIFIED: (a) per-area file + env re-bless
- **Options:** (a) a committed baseline **data file** (`tests/authored_value_baseline.json`) with an
  env-gated updater; (b) an inline expected-count constant in the test; (c) a single grand-total file.
- **Recommendation: (a) a committed baseline data file + env-gated re-bless**, mirroring the golden
  workflow exactly: `PYCATS_UPDATE_AUTHORED_BASELINE=1` regenerates the file (parallel to
  `PYCATS_UPDATE_GOLDENS=1`), and a bump is a **reviewable one-file diff** under author ≠ reviewer.
  Store **per-area** counts, not just a grand total, so a bump diff shows *which* area grew — a new
  guess in nalio and a newly-sourced value in birky must not net to zero and hide.

### Q3 — What exactly does the ratchet gate (direction)? → RATIFIED: authored + undeclared only
- **Ruling:** gate the **authored** bucket (GUESS + PLACEHOLDER) and the **undeclared** bucket: both
  **red on growth, free to drop**. `sourced` and `decided` are reported, not gated. A drop in
  authored/undeclared is surfaced as progress in the test's message. The stretch option — also forbid
  `FOUND` from *dropping* (guard against un-sourcing a value) — is **explicitly out of v1**; it is a
  separate follow-on ticket only if un-sourcing is observed in practice.

### Q4 — Precedent to mirror for the test itself?
- The keyset-equality shape already exists: `test_no_orphans_registry_keyset_matches_curated_names`
  in `test_tuning_provenance.py` reds when an enumerated set diverges from a committed set. The
  ratchet is the *inequality* cousin (count may fall, not rise). Reuse that file's idiom and the
  golden re-bless env-gate; no new test infrastructure is needed.

---

## 7. Suggested follow-on DEV ticket (filed one-at-a-time, after this doc + human review)

**DEV: build the authored-value census + ratchet regression (consumes #1133 seam)**
1. `combat/value_status_census.py` — `census()` reader over `TUNING_PROVENANCE` + the 5 fighters
   (per §4), plus a `__main__`/Make target that prints the table.
2. `tests/authored_value_baseline.json` — committed per-area baseline, `PYCATS_UPDATE_AUTHORED_BASELINE=1`
   re-bless (per §6 Q2).
3. `tests/test_authored_value_ratchet.py` — reds when authored **and undeclared** (per §5, ratified)
   grow above baseline; passes on a drop; prints progress. Must be able-to-fail (add a synthetic
   guess → red; remove it → green) and revert-checked.

All four design questions are ruled (banner at top) — the build is a straight courier task, no
further design gate. Coverage-gate (§5 option a) and the FOUND-drop guard (§6 Q3 stretch) are
**separate, later** tickets if wanted — not bundled.

---

## 8. Out of scope (unchanged from the ticket)
- Building it (the follow-on DEV above).
- Re-sourcing individual values (the #319 sourcing pass).
- CPU constants (#704).

## Refs
#1124 (audit) · #1129/#1133 (the status seam this reads) · `combat/provenance.py` ·
`test_tuning_provenance.py` (keyset-equality precedent) · `test_python_json_drift_guard.py` (R8
hydrate path) · golden re-bless (`PYCATS_UPDATE_GOLDENS=1`) · ADR-0003 · motivating case #1110.
