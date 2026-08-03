# ADR-0003 — Where tuning data + provenance live, and a drift-guard

- **Status:** Accepted  *(2026-06-30 — option (d), the hybrid, ratified by human sign-off; see "Decision point"; #226 / #233)*
- **Date:** 2026-06-29

## Context

pycats sources its combat/physics numbers from canon (Melee/PM via SmashWiki,
rukaidata, the doldecomp/melee decompilation, meleelight, PlCo.dat) and records
*why each value is what it is* — its provenance. Today that provenance is scattered
across **five** places:

1. `pycats/config.py` — inline comments on ~40 combat/physics constants, marked
   `FOUND` / `GUESS` / `TUNED` / `⚠`, citing sources + `#NNN` issues.
2. `pycats/characters/*.py` — per-character/move data with rich provenance in
   docstrings (rukaidata hitbox tables, `round(size × PX_PER_UNIT)` derivations).
3. `GUESSED_VALUES_TO_RESEARCH.md` — a hand-maintained status table (FOUND / GUESS /
   DIVERGENCE per value), owned by umbrella **#192**.
4. `docs/research/*.md` — the deep sourcing narratives.
5. GitHub issue comments (#215, #224, …).

Grounding the scatter (measured in the repo this ADR lands from):
`config.py` declares **138** `UPPER_SNAKE` constants — roughly **40 are sourced
combat/physics tuning** values; the rest are render/UI (colours, screen sizes, HUD
spacing, cat-feature geometry, tail-physics feel knobs). **56** provenance-bearing
comment lines span **9** source files.

**The risk this ADR addresses.** The goldens (`tests/golden/`, see
`REGEN_PROTOCOL.md`) pin *behaviour* byte-for-byte, but **nothing pins *why* a value
is what it is, nor that it still matches its cited source.** A constant can be edited
without touching its citation (`DODGE_AIR_SPEED` drifts from `escapeair_force`), a
derivation can rot (`PX_PER_UNIT` changes; `round(3.1 × PX_PER_UNIT)` no longer yields
the committed literal), or a citation can simply go stale — all silently.

### Constraints (hard)

- **C1 — golden byte-stability (#80).** The sim is pinned to integer pixels; any
  scheme must reproduce **the exact same Python value** as today. A loader/round/float
  reinterpretation that shifts a literal by one ULP breaks every golden.
- **C2 — no new dependency without approval.** Rules out a JSON-schema validator or any
  third-party data/loader lib. `dataclasses` + `pytest` are already available; `tomllib`
  is stdlib but still incurs C1/load/greppability costs (below).
- **C3 — citation discoverability.** A value's source must be greppable and jump-to-def
  navigable from the constant's name.
- **C4 — enforced, not merely documented.** The whole point: the value↔source link must
  be machine-checked, not trusted to comment hygiene.

### Options considered

| | Where data lives | Where provenance lives | C1 golden-stable | C2 no-dep | C3 greppable | C4 enforced |
|---|---|---|---|---|---|---|
| **(a)** status quo | Python constants | inline comments | ✅ trivially | ✅ | ✅ | ❌ comments rot silently |
| **(b)** typed registry, **constants derived** | one typed registry; constants computed from it | same registry row | ⚠ at risk — value is *recomputed* at import; must prove byte-identical | ✅ | ✅ | ✅ |
| **(c)** JSON/TOML + loader | external data files | data files | ⚠ at risk — float parse/round + load order | ⚠ schema lib gated; `tomllib` stdlib but no types/units | ❌ loses symbol jump-to-def | ✅ (needs a checker) |
| **(d)** **hybrid** | Python constants (**unchanged**, bare literals) | a **sidecar registry** keyed by name, data-only | ✅ constants untouched ⇒ automatic | ✅ plain dataclasses + pytest | ✅ | ✅ drift-guard test |

- **(a)** is the status quo whose failure mode *is* this ticket — no C4.
- **(b)** is the tightest "single source of truth" (no value stated twice), but it
  *inverts* C1: deriving the literal from the registry at import makes value-production
  a code path that must be re-proven byte-identical for a sim that is deliberately pinned
  to integer pixels. Needless risk.
- **(c)** is disfavoured on three counts — C1 (JSON floats), C2 (schema lib gated), and
  C3 (a constant stops being a navigable Python symbol) — for no benefit pycats needs.
- **(d)** is the only option satisfying **C1–C4 simultaneously**: constants stay exactly
  as they are (C1 automatic, C3 kept), provenance becomes structured/typed/queryable in a
  sidecar, and a test enforces the link (C4) — all with no new dep (C2).

## Decision

Adopt **(d), the hybrid.** Combat/physics tuning values stay **plain Python constants**
in `config.py` (bare literals at the use-site, byte-identical to today). Their provenance
moves into a **typed sidecar registry** keyed by constant name, plus a **drift-guard test**
that enforces the value↔source link.

**Provenance schema** (frozen dataclass, e.g. `pycats/combat/provenance.py`):

```python
@dataclass(frozen=True)
class Provenance:
    value: int | float          # MUST equal the live constant (C4 anchor)
    unit: str                   # "px/frame" | "frames" | "deg" | "factor" | "%"
    source: str                 # "doldecomp/melee:ftCo_EscapeAir.c" | "SmashWiki:Wavedash" | "rukaidata:PM3.6/Mario/AttackLw3"
    status: str                 # "FOUND" | "GUESS" | "TUNED" | "DIVERGENCE"
    issue: int | None           # GH issue that sourced/changed it
    derivation: str | None = None   # "round(3.1 * PX_PER_UNIT)"; None = not derived
```

**Drift-guard test** (`tests/test_tuning_provenance.py`), three assertions:

1. **No drift** — for every registry name, `getattr(config, name) == prov.value`.
   Catches a constant edited without its provenance (and vice-versa).
2. **No orphans** — an explicit, curated `TUNING_CONSTANT_NAMES` frozenset (the
   combat/physics constants, *excluding* render/UI) must equal the registry's keyset.
   Adding a tuning constant then *forces* a registry row; render/UI constants are
   excluded by construction (no provenance noise on `BG_COLOR`).
3. **Derivation integrity** — every entry with a `derivation` re-evaluates (in a namespace
   of the other constants, e.g. `PX_PER_UNIT`) to its `value`. Catches a derivation rotting.
   Interlocks with **#195**: once `PX_PER_UNIT` is a named constant, `round(3.1 *
   PX_PER_UNIT)` becomes machine-checkable.

**Golden interlock.** Because the constants are byte-unchanged, the migration itself
changes **no goldens** (a green-suite refactor, no regen). Going forward, a tuning-value
change makes the drift-guard go red unless `Provenance.value` + `status`/`issue` are
updated in the same diff — so a value change **forces** a citation update + review, exactly
the "not a silent regen" requirement. `REGEN_PROTOCOL.md` gains a one-line pointer to this.

### Scope of "all our data"

- **In scope (v1):** the ~40 sourced combat/physics scalars in `config.py` — `GRAVITY`,
  `MAX_FALL_SPEED`, `MOVE_SPEED`, `JUMP_VEL`, `DODGE_*`, `WAVEDASH_*`, `SHIELD*`,
  `HITSTUN_*`, `HITLAG_*`, `KNOCKBACK_*`, `SAKURAI_*`, `CROUCH_CANCEL_FACTOR`,
  `KNOCKDOWN_*`, `GETUP_*`, `CLANK_PRIORITY_RANGE`, `JOSTLE_*`.
- **Explicitly excluded:** render/UI constants (colours, screen/HUD/menu sizes, cat-feature
  + tail-physics knobs) — not canon-sourced; the curated set draws this line.
- **Deferred to a later slice (lazy decomposition):** per-character/move data in
  `characters/*.py` (already richly cited in docstrings; structuring per-hitbox into the
  same schema is a bigger, separate slice).
- **`GUESSED_VALUES_TO_RESEARCH.md`:** the registry's `status` field **subsumes** it — the
  GUESS report becomes a `status != "FOUND"` query over the registry. Retiring the
  hand-maintained file is **#192-gated** (that umbrella owns it); v1 represents those
  constants in the registry but does not unilaterally delete the file.

### Decision point (human sign-off)

Per #226, the module-vs-JSON pick was flagged for human ratification. The constraints
(C1 golden-stability + C2 no-dep) make (d) clearly dominant over (b)/(c), but acceptance
of an architecture decision the ticket earmarked for sign-off was the human's call.

**Ratified 2026-06-30 (human sign-off): option (d), the hybrid, is Accepted** (ruling on
#226 / #233). The follow-up refactor **#233** — which was filed blocked on this acceptance —
is now unblocked; this status flip lands as part of #233's implementation.

## Consequences

- **Easier:** provenance becomes typed, greppable, queryable (drives a status report,
  subsumes `GUESSED_VALUES`); the value↔source link is enforced by CI, not comment hygiene;
  a value change can no longer silently desync from its citation.
- **Accepted cost:** each in-scope value is stated **twice** — once as the constant, once as
  `Provenance.value`. This redundancy is *deliberate*: the drift-guard exists to police it
  (edit one without the other ⇒ red test). Plus ~40 registry rows of boilerplate to author
  once during migration.
- **Ruled out:** deriving constants from the registry (b) — keeps C1 automatic; external
  JSON/TOML data files (c) — keeps C1/C3 and avoids dep pressure.
- **Follow-up (refactor DEV ticket **#233**, filed with this ADR; `blocked` on acceptance):**
  1. Add `pycats/combat/provenance.py` (the `Provenance` dataclass + `TUNING_PROVENANCE`
     registry + `TUNING_CONSTANT_NAMES`).
  2. Add `tests/test_tuning_provenance.py` (the three drift-guard assertions). It must be
     **able to fail** — flip a `value` and watch it go red.
  3. Migrate the ~40 in-scope `config.py` comments into registry rows; leave the constants
     **byte-identical** (goldens stay green, no regen).
  4. Add the `REGEN_PROTOCOL.md` pointer.
  Per-character data and the `GUESSED_VALUES` retirement are later, separately-tracked slices.
- **Reversal:** would require a new ADR superseding this one.
