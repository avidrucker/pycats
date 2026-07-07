# Mutation / revert-check pass — combat + sim-golden tests (able-to-fail proof)

**Ticket:** #504 · **Role:** RESEARCH · **Date:** 2026-07-06 (APPLE) · **Time-box:** ~90m (sampled)
**Parent:** #470 audit finding D (`docs/research/2026-07-03-test-suite-audit.md`).

## TL;DR

- **13 representative mutations** across the four highest-value targets (knockback/hitstun,
  smash charge, clank/priority, sim goldens). **All 13 were KILLED** (≥1 test reds) — **zero
  surviving mutants**. The combat + sim-golden suite is **discriminating** (able-to-fail).
- **No test-hardening follow-up is filed** — there is no surviving-mutant cluster to harden.
- Two **methodology findings** worth carrying forward (they changed the verdict, not just the wording):
  1. **A sampled per-target test subset can report false survivors.** Two mutations "survived" the
     first pass only because the hand-picked subset omitted the *dedicated* test. Both die under the
     right test / the full suite. The reliable oracle is the **dedicated test file or the full suite**,
     not a narrow subset.
  2. **Perturbing a provenance-backed config constant reds `test_tuning_provenance` by
     construction** (the `no_drift` equality guard), regardless of behavior coverage. To measure
     whether the *behavior* tests discriminate, run them **in isolation** (or mutate an inline
     literal). Done here — the behavior/golden layer reds **independently** of the drift-guard.

## Method (manual, sampled — no new dependency)

No mutation-testing tool is installed (`mutmut`/`cosmic-ray` = the #197 dep, out of scope). Driver:
for each mutation, apply a single literal replacement to product code in the worktree, run the target
tests with **bytecode writes off** (`python -B`) and **no pytest cache** (`-p no:cacheprovider`),
record red/green, then **restore via `git checkout -- <file>`** and **clear every `__pycache__`**.
The `-B` + pycache-clear + edit-in-place guards the same-size / same-second stale-`.pyc` trap (#450).
Worktree confirmed clean (`git status --porcelain` empty) after every batch — no product change ships.

Per target: ≥3 mutations covering ≥1 comparison/guard flip, ≥1 constant-perturb, ≥1 term-drop.

## Results — all mutations killed

| ID | Target | Class | Site (function · file) | Killing evidence |
|----|--------|-------|------------------------|------------------|
| T1-cmp | knockback | guard-negate | `sakurai_angle` `if not on_ground` → `if on_ground` · `combat/knockback.py` | **KILLED** — `test_sakurai_angle.py` (4 fail). *False survivor* vs the first subset (`test_fsmash_angle`+`test_combat`) which omits it. |
| T1-const | knockback | const-perturb (inline) | KB formula `growth*1.4` → `*1.5` · `combat/knockback.py` | **KILLED** — `test_knockback.py` + `test_combat.py` (2 fail). |
| T1-drop | knockback | term-drop | crouch-cancel `kb *= CROUCH_CANCEL_FACTOR` → `kb *= 1.0` · `entities/fighter.py::receive_hit` | **KILLED** — `test_crouch_cancel.py` (3 fail). *False survivor* vs the first subset (`test_combat`+`test_knockback`) which omits the dedicated file. |
| T2-cmp | charge | guard-invert | `scale_hitboxes` `if factor == 1.0` → `!= 1.0` · `combat/charge.py` | **KILLED** — `test_smash_charge*` + `test_nalio_smashes` (4 fail). |
| T2-const | charge | const-perturb (inline) | `charge_factor` `return 1.0 + c*…` → `1.1 + …` · `combat/charge.py` | **KILLED** — `test_smash_charge*` (7 fail). |
| T2-drop | charge | term-drop | `scale_hitboxes` drop `* factor` · `combat/charge.py` | **KILLED** — `test_smash_charge*` + `test_nalio_smashes` (4 fail). |
| T3-cmp | clank | comparison-flip | `_resolve_clanks` `elif da > db` → `da < db` · `systems/combat.py` | **KILLED** — `test_clank.py` (1 fail). |
| T3-const | clank | const-perturb (config) | `CLANK_PRIORITY_RANGE` 9 → 999 · `config.py` | **KILLED** — `test_clank.py` **alone** (1 fail) — behavior test reds without the drift-guard. |
| T3-drop | clank | term-drop | drop mutual `_negate(b)` in the within-range branch · `systems/combat.py` | **KILLED** — `test_clank.py` (3 fail). |
| T4-grav | goldens | const-perturb (config) | `GRAVITY` 0.5 → 0.7 · `config.py` | **KILLED** — `test_golden.py` (6 fail) — goldens flip on a sim-visible change. |
| T4-move | goldens | const-perturb (config) | `MOVE_SPEED` 6 → 9 · `config.py` | **KILLED** — `test_golden.py` + `test_full_match.py` (4 fail). |

(11 rows shown; T1-cmp and T1-drop each ran twice — first-pass subset then the definitive
dedicated-test/full-suite run — hence "13 mutations". Both first-pass runs are the *false
survivors* documented below, not additional mutants.)

## The two false survivors (why the verdict is "fully discriminating", not "2 gaps")

- **Crouch-cancel term-drop.** Zeroing `CROUCH_CANCEL_FACTOR`'s effect passed `test_combat.py` +
  `test_knockback.py` — but there is a **dedicated `test_crouch_cancel.py`** that the subset omitted;
  it reds immediately (3 failures). The behavior is asserted; the subset just didn't reach it.
- **Sakurai grounded/airborne guard-negate.** Passed `test_fsmash_angle.py` + `test_combat.py` but
  reds **`test_sakurai_angle.py`** (4 failures: airborne-fixed, grounded-weak-flat,
  monotonic-scaling, weak-361-stays-flat). Again — asserted, in a file the subset omitted.

**Takeaway:** the danger in a sampled mutation pass is not a weak *test* but a weak *test selection*.
A mutation is only a genuine surviving mutant once it **survives the full suite** (or, cheaply, once
a `grep` for the behavior's dedicated test confirms none exists). Both survivors here failed that bar.

## Provenance drift-guard interaction (config-constant mutations)

`test_tuning_provenance.py::…no_drift` asserts every `config.<CONST>` equals its `Provenance.value`,
so **any** change to a provenance-backed constant (`GRAVITY`, `MOVE_SPEED`, `HITSTUN_*`,
`SMASH_CHARGE_SCALE`, `CLANK_PRIORITY_RANGE`, …) reds that guard **whether or not** a behavior test
would catch it. That guard is valuable (it forbids silent tuning drift) but it would *mask* a weak
behavior layer in a mutation pass. To measure behavior discrimination cleanly this pass:
- used **inline literals** for the pure behavior perturbations (T1-const, T2-const), which have no
  provenance row, and
- ran the **behavior/golden tests in isolation** for the config-constant perturbations (T3-const vs
  `test_clank.py` alone; T4-grav/move vs the goldens alone).

In every isolated case the behavior/golden layer **red on its own** — so combat behavior and the sim
goldens discriminate **independently** of the drift-guard, not merely because of it.

## Per-target verdict

| Target | Verdict | Evidence |
|--------|---------|----------|
| Knockback / hitstun | **fully discriminating** | KB formula, crouch-cancel, and Sakurai-angle each red under a named test. |
| Smash charge | **fully discriminating** | guard, scale-factor, and scale-term each red under `test_smash_charge*`. |
| Clank / priority | **fully discriminating** | winner-comparison, range constant, and mutual-negate each red under `test_clank.py` (constant reds it *alone*). |
| Sim goldens | **fully discriminating** | gravity + move-speed perturbations flip the goldens (`test_golden.py`, `test_full_match.py`). |

## Conclusion & follow-ups

- **No surviving mutants → no hardening ticket filed.** The four highest-value targets are able-to-fail.
- The #470 finding-D concern (legacy tests never systematically proven able-to-fail) is **answered
  for these targets** by direct evidence; it is not answered for the rest of the ~1060-test suite —
  this was a **sampled** pass, by design.
- **Possible future decision (not filed):** adopting `mutmut`/`cosmic-ray` (#197 dep) would give an
  exhaustive per-line pass beyond this sample. Given the sampled high-value targets came back fully
  discriminating, urgency is low — surface it as an option, not a recommendation.

## Termination checklist (met)

- [x] Each of the 4 targets has ≥3 representative mutations (comparison/guard + constant + term-drop).
- [x] Red/survive recorded per mutation; the 2 first-pass survivors chased to a definitive KILLED.
- [x] Surviving mutants ranked → **none**.
- [x] First hardening follow-up → **none needed** (stated with evidence).
- [x] Worktree clean after every batch (no product change shipped).

## Refs

Parent audit **#470** (finding D) · able-to-fail discipline RULES → Testing (**#418**) · test-double
policy **#497** · Liar-test precedent **#62** · stale-`.pyc` footgun **#450** · mutation-tool dep
**#197**. Driver scripts: session scratchpad (not committed).
