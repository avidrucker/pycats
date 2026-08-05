# Character-value drift — per-fighter movement scalars inheriting the Mario globals

**Ticket:** #1136 (RESEARCH · `area:cross-cutting`) · child of tracker #1134.
**Date:** 2026-08-03 · **Agent:** GRAPE.
**Scope:** findings + option space only. **No value decision, no code change here** — a per-fighter
movement value is a basis-required change, ratified downstream with the human (RULES "Changing a
game value" / "Include human on decisions").

Sibling doc (the audit that seeded this): `docs/research/2026-08-02-magic-number-audit-findings.md`
→ "⚠ Character-value candidates". Prior decision this leans on: **ADR-0011** (per-character grounded
speeds — Accepted 2026-07-31).

---

## TL;DR

1. **The walk / dash / run half of #1136 is already ratified in ADR-0011, not open research.** ADR-0011
   datamined every cat's PM 3.6 walk/dash/run and pinned the roster to them. I re-pulled the primary
   for Mario / DK / Kirby / Marth and it **matches ADR-0011's table exactly**. So Q1 (gnok `run_speed`),
   Q2 (birky `dash`/`run`), and the grounded-speed part of Q3/Q4 are **pending implementation** (ADR-0011's
   un-filed "re-pin" DEV + the open conformance test #957) — **do not re-decide them here.**
2. **The net-new research #1136 adds is the *vertical* scalars ADR-0011 left out** — `gravity`,
   `max_fall_speed`, `jump_vel`, `max_jumps`. Primary values + option space for those are below.
3. **One live inconsistency worth a ruling:** cats disagree on *which* fall speed they model.
   nalio/birky use their archetype's **fast-fall**; gnok uses DK's **base terminal**; narz inherits
   Mario's fast-fall (a drift — Marth's own is different). The `MAX_FALL_SPEED` DIVERGENCE (one global
   fall speed, no base/fast-fall split) is the root.
4. **Q2's premise is refuted by the data.** Kirby's PM 3.6 dash and run are **1.5 u each — identical to
   Mario** (→ 8 px). Birky's inherited `dash=8`/`run=8` is the *correct* sourced value, not a drift;
   Kirby's slowness lives in **walk** (0.85 u, which birky already sets) and air mobility, not dash/run.
5. **Sourcing is a local primary of record.** Every attribute below was **datamined locally** from the
   PM 3.6 `.pac` files via `brawllib_rs @ e8dc833` (env live per #614/#794; clone + `.pac` on disk), and
   **independently cross-confirmed** against rukaidata.com/PM3.6 and `provenance.py`/ADR-0011 — all three
   agree to the digit. This is the stronger primary, not the rendered site.

---

## Method & sourcing

- **Primary — local `brawllib_rs` datamine** (`@ e8dc833`, clone `~/Documents/Study/Rust/brawllib_rs`,
  PM 3.6 `.pac` at `~/Documents/Study/Rust/pm-data/`; env live per #614/#794). Ran from the clone with
  `. ~/.cargo/env` (cargo 1.97.1) against
  `-d …/pm-data/brawl-dump/DATA/files -m …/pm-data/pm36-sd`:
  - grounded walk/dash/run — `cargo run --release --example movement_attrs` (the #814 throwaway; TSV of
    `walk_max_vel`/`dash_init_vel`/`dash_run_term_vel`);
  - vertical scalars — `cargo run --release --example high_level_frame_data -- -f <F> -l fighter`, whose
    `{:#?}` dump carries the full `FighterAttributes` (`gravity`, `term_vel`, `fastfall_velocity`,
    `jump_y_init_vel`, `jump_y_init_vel_short`, `air_jump_y_mult`, `num_jumps`, `weight`). Struct:
    `src/sakurai/fighter_data/mod.rs::FighterAttributes`.
- **Cross-confirmation:** every number below matches `rukaidata.com/PM3.6/<Fighter>/attributes.html` and
  `pycats/combat/provenance.py` / ADR-0011 to the digit — three independent channels agree.
- **Durable artifact:** the full roster's movement attributes — 43 fighters (Pokémon Trainer excluded:
  it is a summoner with no independent physics; Ivysaur/Charizard/Squirtle each carry their own) —
  (walk/dash/run/gravity/term_vel/fastfall/full-hop/short-hop/air-jump-mult/num_jumps/weight, raw PM
  units) are dumped to
  **`docs/research/pm36-fighter-attributes.csv`** — a committed, greppable/spreadsheet reference so the
  correct values never require re-running the datamine. Regenerate with
  `scripts/datamine_fighter_attributes.sh <out.csv>` (loops the stock `high_level_frame_data` example;
  no clone edit; companion to `scripts/datamine_stage_bounds.py`).
- **Conversion seam:** `pycats/combat/units.py` — `u(x) = round(x·PX_PER_UNIT)` (integer, for constant
  speeds — the sim truncates fractions each frame, #80) and `vel(x) = round(x·PX_PER_UNIT, 2)` (float,
  for accelerating rates — gravity/jump). `PX_PER_UNIT = 5.4` (`config/physics.py`).

**Datamined PM 3.6 attributes (raw units, from the local `brawllib_rs` dump):**

| Attribute (`FighterAttributes` field) | Mario | Donkey Kong | Kirby | Marth |
|---|---|---|---|---|
| walk_max_vel | 1.1 | 1.2 | 0.85 | 1.6 |
| dash_init_vel | 1.5 | 1.8 | 1.5 | 1.5 |
| dash_run_term_vel (run max) | 1.5 | 1.8 | 1.5 | 1.8 |
| gravity | 0.095 | 0.1 | 0.08 | 0.085 |
| term_vel (base fall) | 1.7 | 2.4 | 1.6 | 2.2 |
| fastfall_velocity | 2.3 | 2.96 | 2.2 | 2.5 |
| jump_y_init_vel (full hop) | 2.395 | 2.8 | 2.08 | 2.485 |
| jump_y_init_vel_short (short hop) | 1.495 | 1.7 | 1.58 | 1.585 |
| air_jump_y_mult (double-jump) | 0.9 | 1.0 | 0.0 | 1.0 |
| num_jumps | 2 | 2 | 6 | 2 |
| weight | 100 | 114 | 74 | 87 |

Archetype map (`characters/roster.py::ARCHETYPE_ROSTER` + `#779` DK note): **nalio = Mario**,
**birky = Kirby**, **narz = Marth**, **gnok = Donkey Kong**.

---

## What each cat ships today vs. its source

Read from `characters/data/*.json` on this branch. "inherits" = field absent → falls back to the
`FighterData` default (the config global). px column = the datamined unit through the seam.

### gnok — Donkey Kong (`gnok.json`)

| scalar | ships | source (unit → px) | verdict |
|---|---|---|---|
| move_speed (walk) | 6.48 `vel(1.2)` | 1.2 → `u`=6 | value ok; ADR-0011 makes it the **integer** 6 |
| dash_speed | 9.72 `vel(1.8)` | 1.8 → `u`=**10** | ADR-0011 re-pin: 9.72 → **10** |
| **run_speed** | **inherits 8** | 1.8 → `u`=**10** | **DRIFT (Q1)** — runs at the generic 8, slower than its own dash; ADR-0011 → 10 |
| gravity | 0.54 `vel(0.1)` | 0.1 → `vel`=0.54 | ✓ matches |
| max_fall_speed | 12.96 `vel(2.4)` | base 2.4 → 12.96 / fastfall 2.96 → 15.98 | models DK **base terminal** — see fall inconsistency below |
| jump_vel | -15.12 `vel(2.8)` | 2.8 → `vel`=15.12 | ✓ matches |
| max_jumps | inherits 2 | 2 | ✓ **correct** (DK = 2); inheritance is faithful here |
| weight | 114 | 114 | ✓ exact |

### birky — Kirby (`birky.json`)

| scalar | ships | source (unit → px) | verdict |
|---|---|---|---|
| move_speed (walk) | 5 | 0.85 → `u`=5 | ✓ |
| **dash_speed** | **inherits 8** | 1.5 → `u`=8 | **value correct, not a drift** — Kirby dash = Mario's 1.5; ADR-0011 requires an *explicit* bind |
| **run_speed** | **inherits 8** | 1.5 → `u`=8 | same — correct value, needs explicit bind |
| gravity | 0.42 | 0.08 → `vel`=0.43 | ~0.01 low (rounding/design) |
| max_fall_speed | 12 | fastfall 2.2 → 11.88 → 12 | models Kirby **fast-fall** |
| jump_vel | -11 | 2.08 → `vel`=11.23 | ✓ ≈11 |
| max_jumps | 6 | 6 | ✓ exact |
| weight | 70 | 74 | design divergence (birky lighter); weight already per-fighter, out of scope |

### narz — Marth (`narz.json`)

| scalar | ships | source (unit → px) | verdict |
|---|---|---|---|
| **move_speed (walk)** | **inherits 6** | 1.6 → `u`=**9** | **DRIFT** — Marth walks faster than Mario; ADR-0011 Consequences call this out (6 → 9) |
| dash_speed | inherits 8 | 1.5 → `u`=8 | value correct (Marth dash = 1.5); needs explicit bind |
| **run_speed** | **inherits 8** | 1.8 → `u`=**10** | **DRIFT** — Marth run 1.8; ADR-0011 → 10 |
| gravity | 0.45 | 0.085 → `vel`=0.46 | ~0.01 low |
| **max_fall_speed** | **inherits 13** | fastfall 2.5 → 13.5 → 14 / base 2.2 → 12 | **DRIFT** — inherits *Mario's* fast-fall (2.3), not Marth's |
| jump_vel | -12 | 2.485 → `vel`=13.42 | **diverges** — narz bound -12, below Marth's ~13 (design or drift? needs ruling) |
| max_jumps | inherits 2 | 2 | ✓ correct (Marth = 2) |
| weight | 87 | 87 | ✓ exact |

### nalio — Mario, the baseline (`nalio.json`)

Inherits every movement scalar → the config globals, all sourced FOUND against Mario in
`provenance.py` (gravity 0.5, max_fall 13, walk 6, dash 8, jump -13, jumps 2). **Correct by
construction** — nalio *is* the calibration target. The only wrinkle is the `MAX_FALL_SPEED`
DIVERGENCE it inherits (below). Its inheritance is the same inherit-by-omission pattern its own `#557` comment
argued against — the Q4 consistency question.

---

## The four questions, answered (report — not decided)

### Q1 — gnok `run_speed`
**Sourced:** DK `dash_run_term_vel = 1.8 u → u()=10 px` (rukaidata PM3.6/Donkey Kong; = DK's dash, so
run == dash for DK, as for Mario). **Already decided** in ADR-0011's table (gnok run = 1.8 → 10).
Current inherited `8` is a real drift. **No new decision needed — this rides the un-filed ADR-0011
re-pin DEV.**

### Q2 — birky `dash_speed` / `run_speed`
**Sourced:** Kirby `dash_init_vel = 1.5`, `dash_run_term_vel = 1.5` → `u()=8`/`8` — **identical to
Mario.** The audit's "a slow Kirby dashing/running at the generic 8 contradicts its identity" is
**refuted by the primary**: Kirby's dash/run *are* 1.5 u. The inherited 8/8 is the correct magnitude;
ADR-0011 only asks it be **bound explicitly** (no inheritance). Kirby's slowness is walk (0.85, set)
+ air mobility, not ground dash/run.

### Q3 — the Mario-calibrated globals: which cats override, with what
- **walk / dash / run** → **settled by ADR-0011** (roster pinned to PM 3.6; per-cat table above). Not
  re-opened here.
- **gravity** → all cats already bind it except nalio-baseline; birky (0.42 vs 0.43) and narz
  (0.45 vs 0.46) are ~0.01 off their datamined `vel()`. Minor. **Option:** re-pin the two to the
  seam-exact `vel()` value, or leave as within-tolerance design. (`gnok` 0.54 already exact.)
- **max_fall_speed** → the live inconsistency. See next section.
- **jump_vel** → gnok/birky match their source; **narz -12 diverges** from Marth's ~13.42. Report as
  needing a designer ruling (intended lighter jump, or drift?). nalio -13 is FOUND.
- **max_jumps** → **no drift.** gnok/narz inherit 2 (DK/Marth = 2, correct); birky binds 6 (Kirby = 6).
  The one scalar the current inherit-by-omission handles faithfully across the roster.

### Q4 — should every cat bind all movement scalars explicitly?
ADR-0011 **Decision 1** already mandates exactly this for walk/dash/run: "a cat with no speed data is
an **error**, not a default." **The open question is whether to extend that no-fallback principle to
the vertical scalars** (`gravity` / `max_fall_speed` / `jump_vel` / `max_jumps`) so no movement value
is ever inherited-by-omission. Recommendation to put to the human: **yes, extend it** — it closes the
`narz max_fall` / `narz move_speed` class of drift permanently and makes every scalar greppable to a
cited source. This is a decision (schema + regen cost), not a research output.

---

## The fall-speed inconsistency (the sharpest net-new finding)

`MAX_FALL_SPEED = 13` is a registered **DIVERGENCE**: pycats models **one** global fall speed per cat,
with **no Melee/PM base-vs-fast-fall split** (`provenance.py`, cites SmashWiki:Mario_(PM), #120/#384).
Which real value each cat's single number represents is now **inconsistent**:

| cat | ships max_fall | equals its archetype's… |
|---|---|---|
| nalio | 13 (global) | Mario **fast-fall** 2.3 → 12.42 → 13 |
| birky | 12 | Kirby **fast-fall** 2.2 → 11.88 → 12 |
| gnok | 12.96 | DK **base terminal** 2.4 → 12.96 |
| narz | 13 (inherited) | **Mario's** fast-fall (not Marth's anything) |

So three different conventions ship at once: fast-fall (nalio, birky), base terminal (gnok), and
"whatever Mario's is" (narz, by inheritance). Fall speed differs sharply per fighter in PM
(Fox/Falco ≫ Jigglypuff/Peach), so this is a real feel gap, not cosmetic.

**Option space (for a downstream decision ticket — the C4 audit row #557 is the lineage):**
- **(A) Keep the single-global-fall DIVERGENCE, pick one convention, apply it uniformly.** Cheapest.
  Choose fast-fall (matches nalio/birky today, the "committed" feel) → re-pin gnok 12.96 → Kirby-style
  fast-fall `vel(2.96)=15.98`≈16 and bind narz to Marth fast-fall `vel(2.5)=13.5`≈14. One number per cat,
  consistently the fast-fall.
- **(B) Model the base/fast-fall split** (two fields: `fall_speed` + `fast_fall_speed`), re-opening the
  #384/#557 DIVERGENCE. Faithful to PM; largest change (physics + input + data + goldens across every cat).
- **(C) Status quo + document** the per-cat convention so at least it's intentional, deferring the split.

Not choosing here — this needs the human / a designer ruling (RULES).

---

## Provenance / status ledger to carry downstream

For the decision + DEV tickets that follow this doc (values are **FOUND** — local `brawllib_rs @ e8dc833`
datamine, cross-confirmed by rukaidata PM 3.6 — unless noted):

- gnok `run_speed` 10, narz `move_speed` 9, narz `run_speed` 10 → **FOUND**, already in ADR-0011.
- gnok/narz/birky `gravity`, `max_fall_speed` per-cat → **FOUND** magnitudes above; the *fall
  convention* (A/B/C) is a **DIVERGENCE decision**.
- narz `jump_vel` -12 vs Marth 13.42 → currently **unsourced / design** — needs a `TUNED` ruling or a
  re-pin to FOUND.
- All `max_jumps` → already faithful; no row needed.

---

## Sourcing note

The "thorough — datamine env run" ran as a **local `brawllib_rs` dump** (env live per #614/#794 — clone
+ PM 3.6 `.pac` on disk, cargo 1.97.1). Grounded speeds via the `movement_attrs` throwaway; vertical
scalars via stock `high_level_frame_data -l fighter`. No sibling-clone modification (both examples
pre-existed) and no new dependency. Values corroborated by rukaidata.com/PM3.6 + `provenance.py`.
**Doc-hygiene note:** `docs/tooling-brawllib-rs-datamine-recipe.md` still describes the env as
gated/un-run (it predates the `.pac` obtain); #794's §7 has the live paths. A one-line update to the
recipe (point it at the live `pm-data/` paths) would remove that stale gate — flagged, not done here.

---

## Suggested follow-ups (one-at-a-time, downstream of this doc — NOT filed here)

1. **File / surface ADR-0011's un-filed "re-pin" DEV** (walk/dash/run raw-unit JSON schema + drop the
   `MOVE_SPEED`/`DASH_SPEED` globals). It carries gnok `run` and narz `walk`/`run` drift; #957 (open) is
   its conformance test. This is ADR-0011's own follow-up #2 — #1136 just confirms it's still pending.
2. **A decision ticket for the vertical scalars** (ARC): the fall-convention A/B/C ruling, the narz
   `jump_vel` FOUND-vs-TUNED call, and whether to extend ADR-0011 Decision 1's no-fallback rule to
   `gravity`/`max_fall_speed`/`jump_vel`/`max_jumps` (Q4). Research → decision → DEV, per RULES.
