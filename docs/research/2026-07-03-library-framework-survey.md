# Library / framework survey — substantial-help candidates for pycats (#487)

**Role:** RESEARCH (DRAGONFRUIT), 2026-07-03. Survey only — **no dependency installed, no
manifest change, no product code touched**. Every candidate below remains a gated **#197**
adopt/skip decision; this doc produces a ranked shortlist + *proposed* follow-up decision
tickets (listed, not filed).

## Scope & posture (the lens every verdict is weighed against)
- **From-scratch learning project.** A lib that hides the mechanic the project exists to
  learn is flagged even when technically strong (physics, FSM, render loop, AI core).
- **No dependency manifest.** Deps live as README prose (`pygame-ce`, `pytest`,
  sibling `statecharts-py`, plus `imageio`/`imageio-ffmpeg` for video). Adding one is not a
  one-line `requirements.txt` edit — it is a documented, human-approved (**#197**) act.
- **Substantial = one of:** removes hand-rolled code we maintain, closes a
  correctness/coverage gap, or unlocks a blocked initiative. Generic "nice Python lib" is out.
- **Current tooling baseline:** `pytest` (+ `conftest.py`/`pytest.ini`), `pygame-ce`,
  `statecharts-py` (the **sole** live state engine, per README — ADR-0002's dual-backend
  endgame has resolved). No lint config, no type checker, no CI, no coverage tool. `pyflakes`
  sits **undeclared** in the venv (ad-hoc since #193); **#486** (2026-07-03) reverses #198 and
  commits to adopting it.

## Rubric table

| lib | initiative it helps | what it replaces / unlocks | maturity | cost (dep / backlog / learning-goal) | verdict |
|---|---|---|---|---|---|
| **ruff** | code quality / lint | **replaces `pyflakes`** (its `F` rules ≡ pyflakes) + adds import-sort, pycodestyle, pyupgrade; one fast binary, per-rule config + `# noqa` | very high (ubiquitous by 2026) | one dev dep; surfaces the same 141-finding backlog #486 already owns; opinion surface larger than pyflakes | **adopt-now** (as #486's engine, `--select F` first) |
| **pyflakes** | code quality (undefined-name, unused-import) | the tool #486 already chose; minimal single-purpose | high, stable | one dev dep (already #197-approved in #486); **blind on `game.py` star-import**; superseded by ruff on capability | **adopt (decided)** — but see §"#486 reconciliation": prefer ruff as vehicle |
| **black** | formatting | removes style bikeshedding | very high | **redundant if ruff adopted** (`ruff format` is black-compatible); source-diff churn | **skip** (use `ruff format` if wanted) |
| **mypy / pyright** | correctness (typing) | catches the **undefined-name / type-mismatch class pyflakes/ruff-F cannot** (esp. `game.py`, forward-ref annotations) | very high | large backlog surfaced; typing is partly a learning target; setup + annotate effort; pyright = no runtime dep, fast | **adopt-later** (after #486 slice-2 star-import fix) |
| **hypothesis** | sim/physics + testing | property tests for sim **invariants** (knockback monotonicity, FSM transition legality, golden determinism) — a gap the example-based suite structurally can't cover | very high | dev dep; authoring effort; can be slow; **no** learning-goal conflict (it tests, it doesn't replace the sim) | **adopt-later** (high value) |
| **pytest-cov** (coverage.py) | testing infra / DX | quantifies coverage — directly feeds **#470** audit and the known `game.py`-uncovered blindspot | very high | tiny dev dep; no product impact; no learning conflict | **adopt-now** (cheap, high-info) |
| **pytest-benchmark** | `bench.py` | stable timing stats vs the hand-rolled bench harness | high | dev dep; `bench.py` already works — modest marginal value | **adopt-later / low** |
| **syrupy** (snapshot) | render/golden oracles | manages snapshots vs the bespoke byte-identical goldens | high | would replace working hand-rolled golden infra (part of the learning) — low leverage | **skip** |
| deterministic / fixed-point math (e.g. `decimal`) | sim determinism | — | n/a | sim is **already** golden-byte-identical; a fixed-point lib complicates the from-scratch physics | **skip** |
| statechart libs (`transitions`, `python-statemachine`) | FSM backend | would replace `statecharts-py` | high | **direct learning-goal conflict** — the sibling engine is the artifact being learned; ADR-0002 already made it the sole engine | **skip** |
| game-UI / loop libs (`pygame_gui`, `arcade`) | render / screens | replace hand-rolled `screen_manager`/`render_battle` scaffolding | high | fights the from-scratch goal **and** churns render goldens | **skip** |
| behaviour-tree / RL libs | CPU AI | structure beyond the if-then leveled controller | mixed | overkill for the current if-then model (`docs/research/2026-06-30-cpu-ai-decision-model.md`); learning-goal conflict | **skip (v1)** — revisit only if AI complexity grows |
| **pre-commit** | tooling / DX | local enforcement of ruff + pytest on commit | very high | dev dep + config; no CI exists yet to pair with | **adopt-later** (pairs with ruff + #486 enforcement model) |
| CI (GitHub Actions) *(process, not a lib)* | DX / enforcement | the enforcement seam #486 needs (gate pytest + lint) | n/a | setup + maintenance; none today | **adopt-later** (decision, not a dep) |

## Ranked shortlist — top 5 "substantial help"

1. **ruff — adopt-now.** Supersedes `pyflakes`: `ruff check --select F` produces the exact
   pyflakes findings (undefined-name + unused-import) as one fast binary, then extends to
   import-sort/style/pyupgrade per-rule. It is the highest-leverage single adoption and the
   natural vehicle for #486. *Rationale: one tool covers the #486 goal and future lint wants.*
2. **hypothesis — adopt-later.** Property-based tests close the **sim-invariant** coverage
   gap the current example-based suite cannot reach. *Rationale: unique correctness value, no
   learning-goal conflict — it exercises the hand-rolled sim, doesn't hide it.*
3. **pytest-cov — adopt-now.** Cheap, product-neutral coverage numbers to steer the **#470**
   test-quality audit and quantify the `game.py` blindspot. *Rationale: near-zero cost,
   immediately useful to in-flight work.*
4. **pyright (or mypy) — adopt-later.** Catches the undefined-name / type class that
   pyflakes and `ruff --select F` are structurally blind to — the exact `game.py` `NameError`
   family #193 originally reached for. *Rationale: real correctness gain; gate behind the
   #486 slice-2 star-import removal so it can actually see `game.py`.*
5. **pre-commit — adopt-later.** Local enforcement seam for ruff + pytest. *Rationale:
   makes the #486 gate real on each commit without standing up CI first.*

Everything else (black, syrupy, fixed-point math, statechart libs, game-UI libs, AI
frameworks, pytest-benchmark) is **skip or low-priority** — mostly because it either
duplicates a working hand-rolled system or hides a mechanic the project exists to learn.

## Reconciliation with #486 (pyflakes) — **ruff dominates pyflakes**

**Finding:** ruff's `F` rule category is a reimplementation of pyflakes' entire check set
(same undefined-name + unused-import + redefinition rules), plus it is faster, configurable
per-rule, supports `# noqa` suppression (cleaner than pyflakes for the one physics.py
false-positive), and can grow into import-sort/style without a second tool. On capability,
**ruff strictly dominates pyflakes**; there is no check pyflakes has that ruff-F lacks.

**But** #486 (2026-07-03) already (a) reversed #198 to adopt pyflakes and (b) *constitutes the
#197 approval for pyflakes specifically*, and pyflakes is the smaller single-purpose tool that
best matches the minimal-footprint posture. So this is a genuine trade, not a slam-dunk:

- **Recommended:** file the **"adopt ruff (supersede pyflakes)"** decision **before #486
  slice 1 (the ADR)**, so the ADR records the right tool. If accepted, #486 **absorbs** ruff
  by pinning `ruff check --select F` — identical findings to pyflakes today, one binary, room
  to grow — and the rest of #486's plan (declare it, remove the `game.py:26` star-import,
  clean/allowlist the 141-finding backlog, enforcement-model decision) proceeds unchanged with
  ruff in pyflakes' place.
- **Conservative fallback:** if the team prefers the smallest possible surface *now*, keep
  pyflakes as decided; the lateral swap to `ruff --select F` costs ≈nothing later and can be a
  follow-up. Either way, #486's **real value-unlock stays the `game.py` star-import removal**
  (slice 2) — until that lands, any pyflakes/ruff undefined-name check is blind on `game.py`.

**Net:** #486 should **defer its tool choice to the ruff decision ticket below**, then
proceed; the pyflakes *evidence* (backlog shape, game.py blind spot) carries over verbatim.

## Proposed follow-up decision tickets (listed, NOT filed — one at a time)

1. **decision: adopt `ruff` as the lint engine — supersede/absorb pyflakes (#486).** Pin
   `--select F` initially (pyflakes-equivalent); decide whether #486's ADR names ruff. *Blocks
   #486 slice 1 if we want the ADR to record the final tool.*
2. **decision: adopt `hypothesis` for property-based sim-invariant tests.** Scope which
   invariants first (knockback monotonicity, FSM transition legality, golden determinism).
3. **decision: adopt `pytest-cov`** and wire a coverage number into the **#470** test audit
   (+ make the `game.py` uncovered-loop gap a tracked figure).
4. **decision: adopt a static type checker (`pyright` vs `mypy`)** — sequence **after** the
   #486 `game.py` star-import fix so it can see `game.py`; weigh the annotate-backlog vs the
   learning-goal (typing is partly what's being learned).
5. **decision: adopt `pre-commit` + stand up a minimal CI gate (pytest + ruff)** — the
   enforcement-model half of #486 (on-demand vs pre-commit vs CI).

## Method notes / limits (time-box)
- This is a **breadth** survey (H:60m); per-candidate depth (version pinning, exact rule
  sets, backlog sizing, learning-goal debate) belongs in each decision ticket above.
- Maturity read is as of 2026-07; the decision tickets should confirm current release/version
  and any `pygame-ce`/Python-version compatibility at adoption time.
- No candidate was installed or trialled in-repo (per #197 / the ticket's no-install rule);
  verdicts are from capability + fit against the grounded repo state, not benchmarking runs.
