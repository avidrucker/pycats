# TIL 2026-07-19 — GRAPE

**Context:** Executed the ratified skin/Character chain — the last two consumers of
the #755 domain skin-assignment layer: **#718** (the headless sim's 2nd player
defaults to a distinct skin) and **#676** (the live char-select grid tile recolors
to the cycled skin, with a first-come-first-served per-Character skin lock). Both
shipped green; the session's sharper lessons were about *where* work lives (the
worktree) and how easily an uncommitted change can vanish.

---

## 1. The worktree is where the work lives — edit it, run it, review it there

**What happened:** Twice I acted against the **main checkout** instead of the
claimed worktree. On #718 I added the new test to `tests/test_sim_char_palette.py`
in the main repo path and ran pytest there — it reported `no tests ran` because
main didn't have my edit; I reverted main and reapplied in the worktree (error
id=150). On #676 I surfaced the visual-review run command as
`cd $REPO && "$PY" -m pycats.game` pointing at the **main** checkout — which is on
`main` and lacks the worktree's changes. The owner caught it: "are you sure I can
see what's on this worktree with those commands?" I couldn't have — running from
main imports `main`'s `pycats/`, not the branch's (error id=158).

**What I learned:** After `pmtools claim`, *everything* happens in the worktree
dir — edits, `pytest`, and the run command for a human to eyeball unmerged work.
The main-repo `.venv` interpreter is fine to borrow (worktrees have no `.venv`);
it is the **current working directory** that selects which `pycats/` package
`-m pycats.game` imports (cwd is `sys.path[0]` under `-m`). A run command for
pre-merge visual review must therefore `cd` into the worktree, not the repo root.

**The rule:** **Claimed work lives in the worktree — cd there for edits, tests, and
any run/review command; the main checkout only sees a change after it merges.**

---

## 2. `git checkout <file>` to undo a revert-check wipes uncommitted work

**What happened:** On #676 I did a mutation revert-check — edited the grid-draw
loop to drop the skin override, confirmed the tile test went red, then ran
`git checkout pycats/char_select.py` to "restore" it. But the file held my *entire
uncommitted #676 implementation*; checkout reverted all of it to `main`, not just
the one-line mutation. `grep -c` for my new methods returned `0`. I reapplied ~10
edits from context (error id=157).

**What I learned:** This is the known git-checkout-revert-check footgun, and it bit
because the implementation wasn't committed yet. A revert-check needs to restore
*only the mutated hunk*, not the whole file — and `git checkout` on an uncommitted
file restores it to `HEAD` (here, `main`), silently discarding all my work.

**The rule:** **For a revert/mutation check on an uncommitted file, restore the
mutated hunk with an in-place edit — never `git checkout` the whole file, which
reverts every uncommitted change to HEAD.**

---

## 3. `pmtools claim` can mint a branch name that `pmtools close` can't resolve

**What happened:** `pmtools claim <N> --as grape` produced branches like
`br-grape/pycats-718-dev-...` and `br-grape/pycats-676-dev-...` — **missing the
`issue-` token**. `pmtools close`'s `find_worktree_for_issue` matches
`[-/]issue-<N>` in the branch (or a `-issue-<N>` path basename), so on #718 close
failed to resolve the worktree from *every* angle — from main, from inside the
worktree, and even with `--branch`. The other agents' worktrees were the standard
`br-<fruit>/pycats-py-issue-<N>-...`; mine weren't. I recovered with
`git branch -m` to the standard form, after which close ran clean and owned the
merge/push. On #676 and this TIL I renamed **proactively** right after claiming.

**What I learned:** The claim/close branch-name contract can drift, and close's
resolver is strict about the `issue-<N>` token. A rename is safe — it touches only
the local branch name, not `main` — and lets the tool still own the race-safe push.

**The rule:** **Right after claiming, check the branch carries the `issue-<N>`
token; if not, `git branch -m` it to `br-<fruit>/<project>-<lang>-issue-<N>-<slug>`
before you try to close.**

---

## 4. Test a scenario only after confirming the state machine can reach it

**What happened:** For #676's "shared tile shows the most-recently-active player"
rule, I wrote a test that confirmed both players on Nalio, then cycled P1's skin and
asserted the tile followed P1. It failed — the tile read a start-overlay color. The
cause: once *both* players confirm, `CharacterSelector.update` opens the start
overlay and **returns early**, disabling skin cycling entirely. "Both confirmed,
then cycle" is an **unreachable** state in real play.

**What I learned:** I'd tested an imagined interaction, not a real one. I rewrote it
to the reachable behavior — the *last confirmer* owns the shared tile, and
cancelling/backing out releases it to whoever remains — and, since the overlay
confounds a pixel read there, asserted on `_active_skin_by_char` (the documented
state the grid loop paints from) rather than a sampled pixel.

**The rule:** **Before asserting a scenario, confirm the real input path can reach
it; when a render read is confounded, assert on the state the renderer consumes.**

---

## 5. Consuming a ratified domain seam collapses the adapter work

**What happened:** #718 and #676 were both "thin consumer" tickets over the #755
domain layer (`available_skins` for the per-Character pool, `assign_distinct_skins`
for the FCFS lock). #718 became a single de-collide call in `build_players`; #676's
cycle pool and skin lock became calls into the same two functions instead of
bespoke bookkeeping in `char_select`. Neither adapter reimplemented the rules, and
the char-select global-pool bug (any cat could cycle into any base theme) fell out
as a fix for free.

**What I learned:** The #672 epic's "one seam both the sim and live adapters share"
mandate paid off exactly as designed — deciding placement *before* the consumers
started (the #748 architect gate) meant the consumers had nothing to re-derive.

**The rule:** **A consumer of a ratified domain seam calls the layer — it does not
re-implement the rule locally, even when the adapter-local version looks smaller.**

---

## What landed

| Artifact | Change |
|---|---|
| `pycats/sim/runner.py` | `build_players` de-collides same-Character skins via `assign_distinct_skins` (#718) |
| `pycats/char_select.py` | Grid tile recolors to the cycled skin; per-Character cycle pool + FCFS lock; external preview cat retired (#676) |
| `tests/test_sim_char_palette.py`, `tests/test_skin_cycling.py`, `tests/test_char_select_skin_preview.py` | Able-to-fail coverage for distinct-default, per-Character pool, FCFS lock, tile recolor |

## Open threads

- **RULES authority for lesson #1's new wrinkle:** "Surfacing run/sim commands"
  already mandates the `REPO=`/`PY=` block, but not that pre-merge visual review
  must `cd` into the **worktree**. Worth folding a one-line worktree caveat into
  that RULES section (not filed yet — flagging, per suggest-don't-act).
- Lessons #2–#4 are already captured as memories / recurring error rows (ids 150,
  151, 157, 158); #3's claim-side anomaly may deserve a `pmtools` upstream note if
  it keeps recurring.

## Related artifacts

- Domain seam: #755 · architect gate: #748 · epic: #672
- Consumers shipped: #718, #676 · still open downstream: #689 (Phase-1c)
