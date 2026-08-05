# Authored vs sourced vs derived — where value status lives, and where it doesn't

**Ticket:** #1124 (RESEARCH, area:combat) · **Date:** 2026-08-02 · **Agent:** GRAPE
**Motivating case:** #1110 (Birky Final Cutter) — authored phase-2/3 scalars tagged `FOUND` in a close comment.
**Deliverable:** this doc. No code change. Option space only; no decision made here.

## What this answers

Confirms **how and where** the codebase distinguishes three kinds of value:

- **authored** — a playtest starting point / ADR-0003 placeholder / designer guess;
- **sourced** — a datamine/primary observation, labelled `FOUND`;
- **derived** — computed from other sourced/engine numbers (e.g. `round(0.095 * PX_PER_UNIT)`).

## Headline (corrects the ticket's premise)

The ticket says the boundary "is not currently tracked anywhere machine-readable." That is **only half true**, and the correction is the whole point of this audit:

- For **config/physics scalars**, status *is* machine-readable and drift-guarded — the typed `Provenance.status` field in `pycats/combat/provenance.py` (`FOUND` / `GUESS` / `TUNED` / `DIVERGENCE`), enforced by `tests/test_tuning_provenance.py`. This is a real, working status registry (60 rows).
- For **per-fighter move data** — every `characters/*_cat.py` value, including all of Birky's Final Cutter — status exists **only as free-text `.py` comments** and is **entirely absent from the shipped `.json`**. The registry explicitly scopes itself out of this slice.

So the gap is not "no status system exists"; it is "**the status system that exists stops at the config boundary and never reaches fighter data.**" The #1110 mislabel is a symptom of authoring in the un-covered slice, then reaching for the covered slice's vocabulary (`FOUND`) in prose.

A second finding worth stating up front: an audit of the actual code found **no mislabels in the source** — every divergence/placeholder is self-flagged correctly. The #1110 `FOUND` tag lives **only in the GitHub close comment**; `birky_cat.py` and the sourcing doc both call the same values `⚠ playtest starting point`.

---

## 1. The status-marking mechanisms (inventory)

There is a coherent **three-axis** convention, defined in `docs/parity-labeling-legend.md`. Each mechanism below is one part of it, plus the editor guards (which are often confused with the status guards but track something different).

### Axis A — inline source markers (prose / grep-only)

Emoji flags in source comments: `⚠` (guessed / unconfirmed vs PM), `🔬` (sourcing queued), `❓` (undecided design point). Home = the comment on (or above) the value. Machine-readability: **none by design** — the legend even prescribes the grep commands (`grep -rn '⚠' pycats/`). The legend's "convention once" rule says mark a repeated convention in one module docstring, not per line.

Examples: `config/physics.py` `HITSTUN_MULTIPLIER = 0.4  # ... ⚠🔬 verify (Brawl/PM ~0.4)`; `characters/gnok_cat.py` "⚠🔬 playtest starting points (ADR-0003)"; `characters/birky_cat.py` header "Every dy below is a ⚠ playtest starting point (ADR-0003)".

### Axis B — the provenance registry (typed, machine-checked)

`pycats/combat/provenance.py` — `TUNING_PROVENANCE: dict[str, Provenance]`, keyed by the exact config constant name. The `Provenance` frozen dataclass carries `value / unit / source / status / issue / derivation`, and **`status` is the authored/sourced/derived axis**:

- `FOUND` — traced to a cited canon value;
- `GUESS` — unsourced / playtest starting point (a grounding debt);
- `TUNED` — deliberate design value, not seeking canon;
- `DIVERGENCE` — intentional departure from a known canon value.

`derivation` (optional) captures the *derived* case as a re-evaluable string (`"round(0.095 * PX_PER_UNIT, 1)"`; `None` = direct literal). Query views exist: `by_status(...)`, `divergences()` (audit-risk list), `debt()` (the `GUESS` grounding-debt list). This is the single explicit authored/sourced/derived **store** in the repo.

### Axis C — the generated parity light (derived from B)

`docs/parity-status.md` — 🟢 `FOUND` / 🟡 `TUNED`|`GUESS` / 🔴 `DIVERGENCE`-or-absent, regenerated with `python parity_report.py`. A rendered view of Axis B; never hand-authored. Current summary: 24 🟢 / 32 🟡 / 4 🔴 (60 constants).

### The status drift-guard (enforces Axis B)

`tests/test_tuning_provenance.py` asserts, able-to-fail:
1. **no drift** — every registry `value` equals the live `config.<name>`;
2. **no orphans** — the registry keyset equals a hand-maintained `TUNING_CONSTANT_NAMES` frozenset (kept independent *on purpose* so the guard can actually fail);
3. **derivation integrity** — every `derivation` re-evaluates to its recorded `value`;
4. **cross-doc** (#635) — `docs/project-m-rules-by-category.md`'s Status column must agree with the registry;
5. every `DIVERGENCE`/`GUESS` row carries a tracking `issue`.

### Editor R7 / R8 guards — geometry, NOT status (the common confusion)

These do **not** record authored-vs-sourced status. The ticket lists them as an adjacent mechanism, so naming the boundary matters:

- **R7** = `tests/test_drift_guard.py` (#863) — recompiles a JSON's per-frame `provenance` block through R6 `collapse` and asserts it reproduces the committed `hitboxes`. It guards **hitbox geometry** against its own frame-trace. (The four shipped fighters were migrated with no per-frame trace, so the shipped sweep is vacuously green today.)
- **R8** = `tests/test_python_json_drift_guard.py` (#877) — asserts a flipped fighter's shipped JSON equals its Python oracle (`load_fighter_data(stem) == <STEM>_FIGHTER_DATA`).

The per-frame `provenance` block R7 checks is a *frame-trace*, not a `FOUND`/`GUESS` label. So `pycats/combat/provenance.py` (value status) and the editor's per-frame `provenance` JSON block (geometry) are **two different things sharing a word**.

### Not a status registry: `docs/decisions-ledger.md`

ADR-0007's append-only ruling table. Its own header **excludes** per-value provenance and points at `provenance.py` instead. It records design *rulings* (e.g. #704 "CPU tuning as pycats-custom flavor, not PM parity"), which *authorize* a `TUNED`/`DIVERGENCE` status but don't store it.

### Legacy, superseded: `GUESSED_VALUES_TO_RESEARCH.md`

A hand-maintained FOUND/GUESS/DIVERGENCE table at repo root that ADR-0003 says the registry `status` field subsumes ("the GUESS report becomes a `status != 'FOUND'` query"). Retirement is #192-gated, so it lingers but is superseded.

**Coverage summary**

| Mechanism | Records value status? | Machine-readable? | Home |
|---|---|---|---|
| Axis A `⚠`/`🔬`/`❓` markers | flags authored/unresolved | grep-only (prose) | source comments |
| Axis B `provenance.py` registry | **YES** — FOUND/GUESS/TUNED/DIVERGENCE | **yes** (typed + drift-guard) | `pycats/combat/provenance.py` |
| Axis C parity light | derived view of B | generated | `docs/parity-status.md` |
| `test_tuning_provenance.py` | enforces B↔config↔manifest | yes | `tests/` |
| Editor R7 (`test_drift_guard.py`) | no — hitbox geometry | yes | `tests/` |
| Editor R8 (`test_python_json_drift_guard.py`) | no — JSON vs Python oracle | yes | `tests/` |
| `decisions-ledger.md` | no — design rulings | markdown | `docs/` |
| `GUESSED_VALUES_TO_RESEARCH.md` | legacy table (superseded) | markdown | repo root |

---

## 2. Where authored vs sourced values actually live

| Area | File(s) | How declared | Status recorded? |
|---|---|---|---|
| **Fighter data** | `characters/*_cat.py` + `characters/data/*.json` | frozen dataclass literals (`.py`); compiled numeric form (`.json`) | `.py`: inline prose only (⚠ playtest / FOUND / MEASURED / `human-designer-temporary-placeholder`). **`.json`: none at all.** No typed registry. |
| **Physics/config** | `config/physics.py`, `config/stage.py`, `config/*`; seam `combat/units.py` | module-level literals | Inline ⚠ comments **plus** the typed `provenance.py` registry, drift-guarded. The only machine-enforced slice. |
| **CPU controller** | `sim/controllers.py` | literals + `LEVEL_PARAMS` dataclass table | Inline ⚠ comments **only**; **explicitly outside** the registry (self-documented). |
| **Stage bounds** | `config/stage.py` | literals | Split: `BLAST_PADDING`/`_TOP` registered `TUNED`; `BLAST_PADDING_X` deliberately unregistered (temporary #733); platform consts unannotated. |

Detail worth keeping:

- **Fighter `.py`** carries the richest prose but no structure. Marker counts (`grep -c` of the status words): birky 21, nalio 21, gnok 15, narz 14, default 2. Styles vary per author — nalio uses one file-level convention marker (per the #120 "convention once" rule); gnok uses `MEASURED` for body geometry and flags a faithful-vs-tuned velocity split; birky uses per-move `⚠ playtest starting point` and a distinct `human-designer-temporary-placeholder-values-for-v1-only — NO parity claim` for the #893/#911 sex-kick flattening.
- **Fighter `.json`** is the shipped/loaded form and carries **zero** provenance: a grep for `FOUND|GUESS|TUNED|status|source|playtest|⚠` across all five JSONs returns nothing. Whatever status a value has is lost the moment it is compiled to JSON — and the JSON is what the editor and drift-guards actually read.
- **`combat/units.py`** holds no game constants — it is only the px↔unit seam (`u()`, `vel()`), importing `PX_PER_UNIT`. Correct target for "derived" derivations.
- **CPU constants** (`JUMP_COOLDOWN`, `EDGE_HOG_RANGE`, `SMASH_KILL_PERCENT`, the `LEVEL_PARAMS` anchors, the #970 smoothing block, …) are self-documented as *outside* the registry, following the "`controllers.py` ⚠-comment convention rather than a combat/provenance row." Confirmed: none appear in `TUNING_CONSTANT_NAMES`, so no drift-guard covers them.
- **Intentional registry omissions** (honest gaps, not mislabels): `BLAST_PADDING_X` (temporary #733), `LEDGE_POST_CUTOFF_RESIDUAL_FRAMES` (`# PLACEHOLDER_VALUE_PLS_RESEARCH_ACTUAL`, "carries NO Provenance entry ... an acknowledged gap", #656).

---

## 3. The gaps (grounded, prioritized)

**G1 — Fighter/move data has no structured status seam at all (the core gap).**
Every per-character value — spike/beam scalars, dx/dy placements, per-move damage/angle/knockback — lives outside `provenance.py` by explicit design ("Per-character/move data in `characters/*.py` is a later slice"). Status is free-text `.py` prose, unenforced, and stripped entirely from the `.json`. This is where the #1110 values sit, and why the boundary between authored and sourced there is invisible to any tool. **Highest priority** — it is the whole motivation.

**G2 — The compiled `.json` loses all provenance.**
Even for a fighter value that *is* carefully labelled in `.py`, the shipped `.json` (what loads at runtime and what the editor round-trips through R7/R8) has no status field. A status seam for fighter data has to decide whether status rides in the JSON or stays a `.py`-only annotation regenerated on flip.

**G3 — The #1110 mislabel is real but prose-only.**
The #1110 close comment stamps the authored phase-2/3 list — plunge frame 38, plunge vy 12.0, spike dmg 6.0 / bkb 30 / kbg 80, beam speed 8.0 / lifetime 20 / dmg 5.0 / bkb 25 / kbg 70 — as `(FOUND, ADR-0003 class)`, conflating "playtest starting point" (authored) with `FOUND` (sourced). `birky_cat.py` and `docs/research/2026-07-31-birky-final-cutter-sourcing.md` both label them `⚠ playtest starting point` correctly; the sourcing doc reserves `FOUND`/`FOUND-derived` strictly for phase-1 rise scalars, `radius u(3.5)=19`, `recovery_vy ≈ -15.7`, `recovery_vx = 0`, plus `landing_lag = 35` (PM `SpecialAirHi4`). So there is **no code or doc to fix** — the corrective action is a close-comment/record note, and, longer term, a seam (G1) that would have made the prose claim checkable.

**G4 — CPU constants are a deliberate but untracked slice.**
Self-documented as outside the registry. Not a mislabel, but a whole class of values whose status no tool can query. Worth an explicit decision: fold into a future fighter/AI status seam, or leave as convention.

**No G for "mislabels in source":** the code audit found none. `MAX_FALL_SPEED`→`DIVERGENCE`, `BLAST_PADDING_X`→unregistered-temporary, `LEDGE_POST_CUTOFF_RESIDUAL_FRAMES`→acknowledged-gap, and Birky's phase-2/3→`⚠ playtest` are all labelled correctly. The repo is disciplined; the failure mode is *coverage* (whole slices with no typed status), not *wrong labels*.

---

## 4. Option space for a machine-readable fighter-data status seam (no decision)

This is the input to the follow-on RESEARCH ticket (the tracking-system design). Options are sketched, not chosen.

**Where the status could live:**

- **O1 — Extend `provenance.py` to per-move keys.** Add rows keyed by `<cat>.<move>.<field>` (e.g. `birky.up_b.spike.damage`). Reuses the existing `status` vocabulary, drift-guard, and Axis C rendering. Cost: the registry balloons from ~60 scalars to hundreds of per-frame/per-box values; the "no orphans" guard would need a fighter-data keyset. The ADR-0003 scope note ("later slice") anticipated exactly this extension.
- **O2 — A status block inside the fighter `.json`.** Add an optional `status`/`provenance` field per move or per value in `characters/data/*.json`, regenerated from `.py` on flip. Fixes G2 (status survives compilation) and is what the editor/R7/R8 already read. Cost: schema-version bump; every fighter JSON regenerated; the flip pipeline must carry status from `.py` to `.json`.
- **O3 — A typed annotation on the `.py` dataclasses.** Give `Hitbox`/`MoveData` an optional `status` field (defaulting `None`) so authored-vs-sourced becomes a real attribute, not a comment. Naturally flows into O2's JSON if the flip serializes it. Cost: touches `combat/data.py` and every `*_cat.py` construction site.
- **O4 — Leave fighter data as prose; formalize a lint.** Keep `.py` comments but add a grep/AST lint that requires every authored fighter value to carry a `⚠`/status marker, mirroring Axis A. Lowest cost, no schema change; but stays grep-only and never reaches the JSON (G2 unsolved).

**Cross-cutting questions the design ticket must settle:**

- Does status ride in the shipped `.json` (O2/O3) or stay `.py`-only (O1/O4)? This is the G2 fork.
- Is the vocabulary the existing four (`FOUND`/`GUESS`/`TUNED`/`DIVERGENCE`) verbatim, or does fighter data need a fifth (e.g. the `human-designer-temporary-placeholder` case, or `MEASURED` for body geometry)?
- Are CPU constants (G4) in or out of the same seam?
- Granularity: per-value, per-box, or per-move? (Per-value is precise but heavy; per-move is coarse but cheap.)

**Sequencing note:** building any of O1–O4 is explicitly out of scope here and is the follow-on ticket. The #1110 corrective note (G3) is small and separable — it can be a one-line record correction independent of the seam.

---

## Refs

`pycats/combat/provenance.py` · `docs/parity-labeling-legend.md` (the three-axis system) · `docs/adr/0003-tuning-data-provenance-and-drift-guard.md` · `tests/test_tuning_provenance.py` · editor guards `tests/test_drift_guard.py` (R7) / `tests/test_python_json_drift_guard.py` (R8) · `docs/parity-status.md` (generated) · `docs/decisions-ledger.md` (ADR-0007) · `GUESSED_VALUES_TO_RESEARCH.md` (legacy) · `pycats/sim/controllers.py` (CPU slice) · `pycats/config/stage.py` (stage bounds) · `docs/research/2026-07-31-birky-final-cutter-sourcing.md` (FOUND-vs-playtest exemplar) · #1110 (motivating mislabel) · #1095 (Birky tuning tracker).
