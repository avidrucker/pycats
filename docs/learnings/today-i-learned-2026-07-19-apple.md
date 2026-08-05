# TIL 2026-07-19 — APPLE

**Context:** Reverse-applied the rewritten `verify-claims` skill to pycats' `claims-data/` ledger, and in the process migrated `.claude/ledger.json` to its new 7-key schema (#757). That migration left a red test on main, which surfaced a chain of process lessons (#762, #764) and a real upstream `pmtools` bug (pmtools#135). Also decomplected the CPU ledge-getup problem into an epic (#751 → #754, superseding #722).

---

## 1. Split a skill migration by git-trackedness — the trackedness boundary is the commit boundary

**What happened:** The `verify-claims` new model needed a lot of reshaping: add `draft-claims.md`/`cancelled-questions.md`, drop the retired `evidence/` dirs and per-topic `INDEX.md`, give the root its own lifecycle file-set, delete the stale `README.md`/`rubric.md`, and migrate `tooling/`'s evidence tokens (`[E1·query]` → `[query]`). All of that is under `claims-data/`, which is **git-excluded**. Exactly **one** file in the whole migration is tracked: `.claude/ledger.json`.

**What I learned:** The git-excluded bulk needs no commit at all — it's durable working material that just lives in the main checkout. The single tracked file is the only thing that needs a commit, and because it's unrelated to whatever ticket I happened to be claimed on (#754, a PM-ledge research ticket), it must route through its **own** chore ticket (#757), not ride along — the `pmtools close` scope audit (`git diff merge-base..HEAD`) would flag a config change smuggled into a research branch.

**The rule:** **In a mixed migration, let git-trackedness draw the commit boundary — the git-excluded working files need no ticket; each tracked file routes through a ticket scoped to it.**

---

## 2. "Not our bug" and "a real upstream bug" can both be true — reading the source is what separates them

**What happened:** `pmtools close 757` failed with *"no worktree for issue #757 found"*, even from inside the worktree and with `--branch`. It looked like I'd misnamed a worktree. Reading the source said otherwise: `pmtools` **#128** had switched minting to a `standard` shape (`br-<agent>/<project>-<N>`), deliberately dropping the `issue-` token — so `br-apple/pycats-757` was *correct*. But `find_worktree_for_issue` (`py/close_core.py`) and three sibling gates still hardcoded `[-/]issue-<N>`, even though the tolerant `CANONICAL_*` parsers already existed in `claim_core.py`. So the failure was **two** separate things: (a) pycats-side config/docs drift — `.claude/orchestrate.json`'s `worktreeBranchPattern` and RULES still describe the legacy shape (filed #759), and (b) a genuine **incomplete #128 migration** in pmtools (filed pmtools#135).

**What I learned:** My first instinct ("did we misname?") and the truth ("the shape is canonical; the resolver lagged the mint") were only separable by reading the two functions. GRAPE hit the *same* wall the same day (their err #151), working around it with a manual `git branch -m` on every close — a recurring tax. Filing pmtools#135 fixed it upstream so the workaround retires for everyone.

**The rule:** **When a tool rejects a name, read the minter and the resolver before blaming the name — a canonical name a stale consumer can't parse is the consumer's bug, and it's worth filing upstream, not working around forever.**

---

## 3. Run the full suite after your FINAL edit — the `pmtools close` gate is ruff-only, not pytest

**What happened:** I left a red test on main. In #757 I ran the full suite in the worktree — green, 1367 passed — **before** editing `ledger.json`, then edited (dropping `evidenceDir`), committed, and closed with no re-run. `tests/test_ledger_config.py` still required `evidenceDir`, so it went red. It merged anyway because the close verify gate is `ruff format --check` + `ruff check` on `pycats/` only (`close.verify` in `.claude/orchestrate.json`) — **it never runs pytest**. A green close is not a green suite. Discovered only when the owner asked "did you leave red tests on main?"; fixed in #762, codified in #764.

**What I learned:** The existing "run the suite right after claiming" rule guards the *merge race* (inheriting another agent's red), but not the red *I* introduce with my own later edits. And ruff has nothing to say about a broken Python assertion. Two independent gaps let it through. A repo-wide `evidenceDir` grep would also have found the guarding test before I removed the key.

**The rule (→ #764):** **Re-run the full suite after your final edit, not only after claim; a successful `pmtools close` proves ruff, never pytest — and grep for a test that guards any config/data file you change.**

---

## 4. A green close is circular for a schema change — dogfooding proves the fix

**What happened:** #762 closed with a **standard-form** worktree (`br-apple/pycats-762`, no `issue-` token) and **no** `git branch -m` workaround — the close resolved it cleanly. That was live confirmation that pmtools#135's fix works, verified by *closing*, not by re-reading the patch.

**The rule:** **Confirm an upstream fix by exercising the exact path that failed, not by reading that the patch merged.**

---

## 5. Demote self-verified claims — verifier ≠ asserter is a hard gate

**What happened:** The `tooling/` ledger's three claims read `Asserted by CLAUDE` / `Verified by CLAUDE-VERIFIER` — a self-verification the rewritten `verify-claims` model forbids (a **human** ratifies verification). I demoted all three verified → unverified: **MOVE** (not copy), keep the ID, add `Falsified-by` + `How to verify`, drop the verified-only `Verdict`/`Entails`.

**What I learned:** `bad` ≠ `FALSE` ≠ `unverified`. A self-certified claim is none of those failure modes — it isn't refuted and it isn't malformed; it's simply **unproven** until a second party judges it. The demotion preserves all the evidence and the ID; only the lifecycle file changes.

**The rule:** **A claim whose asserter and verifier are the same author isn't verified — move it back to `unverified` with its evidence intact, and let a human ratify.**

---

## What landed

| Artifact | Change |
|---|---|
| `.claude/ledger.json` | Migrated to the verify-claims 7-key schema (drop `evidenceDir`, add `topics`/`testDir`) — **#757** (closed) |
| `tests/test_ledger_config.py` | Fixed red main: `REQUIRED_KEYS` → 7-key schema + `evidenceDir`-retired guard — **#762** (closed) |
| `claims-data/` (git-excluded) | Root+topics reshape to the new model; `tooling/` token migration; 3 claims demoted; `ledge-getup/` topic scaffolded |
| **#759** (open, BANANA) | pycats `worktreeBranchPattern` + RULES drift to the #128 standard shape |
| **#764** (filed) | RULES: re-run after final edit; the close gate is ruff-only |
| **pmtools#135** (closed/merged) | Incomplete #128 migration — resolvers routed through `CANONICAL_*` |
| **#751 / #754** | CPU ledge-getup epic + tight A1 (superseding #722) — decomplect (PM only) |

## Open threads

- #759 (BANANA) and #764 still to land; once #759 merges, an agent reading RULES/config will no longer read a standard-form worktree as misnamed.

## Related artifacts

- [TIL 2026-07-19 GRAPE](./today-i-learned-2026-07-19-grape.md) — hit the same pmtools branch-resolver wall (err #151); this session filed it as the upstream fix pmtools#135.
- Issues #757, #762, #764, #759, #751, #754; pmtools#128, pmtools#135.
