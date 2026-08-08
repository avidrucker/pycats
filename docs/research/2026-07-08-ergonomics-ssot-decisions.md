# Ergonomics + SSOT hygiene — decision rationale (record of #724)

**What this is:** the durable "why" behind tracker **#724**. #724 records *what* was decided
and a one-line shape per item — enough to execute a child. This doc records *why* each verdict
came out as it did (the `yegor-personas` council readings), the SSOT-layering diagnosis that
framed the whole review, and the dependency reasoning — so a future agent can **re-evaluate** a
decision, not just execute it.

**Provenance:** session of 2026-07-08 (ELDERBERRY). Each decision was run through
`guide-human-decision` + `yegor-personas` and confirmed by Avi one at a time. This records the
reasoning; it does not reopen it. Once the #705 append-only Decision Log ledger exists, this
content migrates there; until then this doc is the home.

---

## 1. The framing — SSOT-layering diagnosis

The trigger question was "are we storing mechanics/rules in too many places?" The finding: the
count isn't the problem — **ownership** is. "Mechanics and game rules" is five distinct concerns,
and each should have exactly one authoritative home; everything else is a **pointer** or a
**test-guarded derived copy**.

| Concern | The one SSOT | Everything else should be |
|---|---|---|
| **Value** (what the number is) | `pycats/config.py` (bare literal, no loader) | read-only consumers |
| **Why** (source/unit/status) | `combat/provenance.py` `TUNING_PROVENANCE` | drift-guarded copy of the value |
| **Behavior** (how it works) | the code — `charts/`, `combat/`, statecharts | executable = SSOT by construction |
| **Description** (for humans) | `pm-reference/` (faithful) · `custom-pycats-mechanics.md` (invented) | glossary = pointer only |
| **Decision** (why we chose it) | the #705 decisions-ledger / ADRs | issue threads = history, not SSOT |

**The pattern that already works:** `config.py` ↔ `provenance.py` state the same value twice on
purpose, and `test_tuning_provenance.py` reds if they diverge. Duplication is fine when one copy
is authoritative and a **test enforces equality**. The whole rollout replicates this pattern for
the prose layer.

**Where SSOT actually leaks today (the four gaps):**
1. **Prose sprawl** — ~30 top-level docs + 19 `pm-reference/` + 70 `research/`, several views of
   the same mechanic with no declared owner (five parity-flavored files, no keep-list).
2. **Per-character/move data has no drift-guard** — `provenance.py` scopes itself to `config.py`
   scalars; `characters/*.py` values (many ⚠ playtest) are unguarded. The biggest real hole.
3. **Descriptions have no mechanical link to code** — prose describes behavior; nothing reds when
   a landmark is renamed (unlike the value layer).
4. **Rationale trapped in issues** — much "why" lives only in ticket bodies/comments.

**Net:** one solid value SSOT + a prose layer with no ownership rules and no drift-guard. The fix
is a **pointer-first contract + a router index + a landmark guard** — the rollout in #724.

---

## 2. Per-item council rationale

Format: personas **with standing** (not all 17), the pivotal reading(s), the convergence, and the
**authority** that settled it (Yegor's ladder: requirements → binary gate → objective measure →
reporter → architect → no-compromise).

### #1 — Makefile as command SSOT · **YES, now**
- **Seated:** microtasks, nohelp, architect, PO.
- **Pivotal:** microtasks — bounded ≤60m artifact (objective PASS). nohelp — a Makefile that
  hardcodes the commands becomes a *second* copy of the README's run line → drift; only safe if it
  **becomes** the command SSOT and README points at it. architect — worktrees have no `.venv`, so a
  naive `.venv/bin/python` breaks from a claimed worktree; done right it *encapsulates* the
  main-venv resolution (via `git rev-parse --git-common-dir`, as the close-gate does) — raising the
  value.
- **Convergence:** yes now, the top opener; shaping condition = Makefile is the command SSOT,
  README references it. **Authority:** microtasks (objective, rung 3) — nothing to vote on; nohelp
  shapes *how*, not *whether*.

### #2 — `docs/` doc map + status legend · **thin half only, folded into #4**
- **Seated:** spikes, microtasks, architect, nohelp, PO.
- **Pivotal:** spikes — classifying ~120 files where several need *reading* to judge stale-vs-live
  is spike-shaped, not a clean index task (objective NO to the full standalone version). architect —
  it's two artifacts: a thin authoritative index (overlaps #4) and a full-corpus classification
  (that's #7). microtasks — thin ≤60m; full is L.
- **Convergence:** do the thin authoritative index, **folded into #4's router** (one front matter,
  not two competing indices); route the full classification to #7(b). **Authority:** spikes
  (objective, rung 3) settles that the full version isn't a one-shot index.

### #3 — one agent front door in CLAUDE.md · **DEFER — capstone**
- **Seated:** architect, nohelp, microtasks, review.
- **Pivotal:** architect — CLAUDE.md is *already* injected into every session, so a front door adds
  ordering, not a new surface; and two of its four link targets (`make`, mechanics-index) don't
  exist yet → linking vapor, rework guaranteed. review — the real failure mode is *adherence*, not
  *discovery*: recurring slips (banned words, read-before-edit, verify-ticket-numbers) are on rules
  *already loaded and flagged IMPORTANT*, so re-ordering them is marginal.
- **Convergence:** defer; build last, after #1+#4, as the tie-together capstone. **Authority:**
  architect (rung 5, sequencing) + the plain fact that its deps are unbuilt.

### #4 — `docs/mechanics-index.md` router · **YES — keystone, bound to #5**
- **Seated:** architect, nohelp, review, microtasks, pdd.
- **Pivotal:** architect — the keystone (#2A folds in, #3 caps it, #7 uses it as the keep-list);
  ~80% of its content already exists as the #605 inventory → **promote, don't build**; and a
  hand-kept 4-pointers-per-row table with **no guard is a new rot surface** — the exact disease
  being treated. review — premature-abstraction skeptic + the drift irony. microtasks/pdd — **cap
  to the provenance-registered set**; defer per-character rows to puzzles.
- **Convergence:** yes, with three conditions — (1) bind #4+#5 as one unit, (2) build by promoting
  #605, (3) cap the keyset. **Authority:** architect (rung 5, design) — the router and its guard are
  one work item.

### #5 — doc-landmark resolution test · **YES — the guard half of #4**
- **Seated:** unit-tests, TST, architect, bdd, review.
- **Pivotal:** unit-tests — real-vs-Liar *flips on scope*: over #4's structured `pkg/mod.py::Symbol`
  column it's a genuine able-to-fail guard; over freeform prose across 120 docs it's an
  allowlist-bloated Liar that gets disabled. TST — deterministic only if the input is structured.
  architect — solve the parser by **structuring the input** (AST resolution, no import side effects),
  not by smartening regex.
- **Convergence:** yes, scoped to #4's structured column, AST-based, small allowlist. The coupling is
  mutual: #4's strength depends on #5, and #5's *feasibility* depends on #4 being structured → **one
  unit**. **Authority:** unit-tests + TST (objective, rung 3) on "real vs Liar"; architect on the
  parser design (rung 5).

### #6 — extend the drift-guard to per-character/move data · **NOT now — spike + sequence after #672**
- **Seated:** microtasks, spikes, architect, REQ/PO, bdd.
- **Pivotal:** microtasks — L/multi-session, must decompose (objective NO to "now"). spikes — field/
  move corpus + keying scheme unsurveyed → spike-first (objective). architect + REQ/PO — the read-
  *location* is a moving target: #672's domain migration (`fighter_data_of`/`build_fighter`, #680/
  #686) is actively relocating the per-character mechanics home, so a guard built now keys against a
  layout about to move → rework is certain, not risked.
- **Convergence:** highest value overall, worst timing. Scoping spike alongside the #672 tail →
  implement after #672; mark `Sequenced after: #672`; owned by the #672 line, not this organizing
  effort. **Authority:** microtasks + spikes (objective, rung 3) settle "not now as one task";
  architect/REQ (rungs 5/1) settle the sequencing.

### #7 — quarantine stale artifacts · **SPLIT — low urgency**
- **Seated:** microtasks, architect, review, nohelp, TST.
- **Pivotal:** microtasks — named targets (2 `*_FIX_SUMMARY.md`, ~10 `scripts/` debug files) are
  bounded; "which parity docs are superseded" needs judgment → split. architect — folding into one
  *authoritative* parity doc presupposes the keep-list = #4 → part (b) sequences after #4. review —
  **archive-not-delete** (reversible) and look-before-you-delete; confirm a script's assertions live
  in `tests/` and a doc's content is captured before it dies.
- **Convergence:** (a) archive dead named files + triage the debug pile — anytime, low urgency,
  archive-not-delete; (b) parity consolidation — after #4. **Authority:** microtasks (objective
  split) + architect (sequencing) + the global look-before-delete rule.

---

## 3. Dependency reasoning (why the waves are shaped this way)

- **#4 + #5 are one unit.** A router unguarded is a fifth pointer-copy that rots (the very disease);
  a landmark test over freeform prose is a Liar. Structuring #4's landmark column makes #5 feasible,
  and #5 makes #4 self-defending. Neither ships alone.
- **#6 is sequenced after #672.** #672 relocates the per-character mechanics data (`fighter_data_of`,
  `build_fighter`) that #6's guard would key against — building before it lands guarantees rework.
- **#3 is a capstone after #1 + #4.** It links their live targets; built earlier it links vapor.
- **#2 folded, not dropped.** Thin authoritative index → #4; full-corpus classification → #7(b).
- **#7 split.** (a) dead named files = anytime side-pass; (b) parity consolidation = after #4's keep-list.

**Authority-ladder note:** several verdicts settled on *objective* rungs, not a vote — the ≤60m
`microtasks` budget (#1 yes, #6 no) and `spikes`' "is scope clear?" (#2 full-classify no, #6
spike-first). Those are reported as measurements, not opinions. The design ties (#4/#5 as one unit,
#3 sequencing) fell to the architect (rung 5). No decision required the no-compromise rung — none
ended in an unresolved split.

## Refs
Tracker **#724** (decisions of record). Inventory that seeds #4: **#605**
(`docs/research/2026-07-07-custom-mechanics-inventory.md`). Future ledger this migrates into:
**#705**. Data-model migration that gates #6: **#672** (#680/#686). SSOT pattern precedent:
`combat/provenance.py` ↔ `tests/test_tuning_provenance.py`.
