# TIL 2026-07-30 — ELDERBERRY

**Context:** A `area:docs` run — shipped the run-command helper (#859), then cleaned
up after myself: the helper's own test reddened `main` fleet-wide (#895), and the
README's `make` docs had drifted from `make help` (#892). Filed a drift-guard
follow-up (#896). The through-line: tooling that *generates* the right answer beats
prose that *describes* it, and tests must not be coupled to the worktree they were
born in.

---

## 1. A generator beats prose for a recurring mistake

**What happened:** #859 existed because agents kept handing the human a run command
that pointed at `main` for code living on a worktree branch — running the *old*
build and "testing" the wrong thing. The guidance already existed in RULES.md
§"Surfacing run/sim commands"; prose hadn't stopped it (errors DB rows 164, 221,
…). The fix was a command that *emits* the exact string: `make run-cmd
WHAT=<issue|branch|path>` → `cd '<worktree>' && make run`. Because `make run`
already resolves main's `.venv` from a worktree cwd, the generated form has no
hand-typed path to get wrong.

**What I learned:** When a documented rule keeps getting violated, the failure isn't
that people don't know the rule — it's that following it requires assembling
something by hand. Replacing the prose recipe with a generator (and repointing the
docs at the generator) removes the hand-assembly step where the error lived.

**The rule:** **When prose guidance keeps getting violated, ship a generator that
produces the exact artifact and repoint the docs at it — don't just reword the
prose.** (Authority: #859; RULES.md §"Surfacing run/sim commands" now points at the
helper.)

---

## 2. An e2e test coupled to its authoring worktree reddens main fleet-wide

**What happened:** In #859 I wrote `test_cli_resolves_this_worktree_from_its_issue_number`
that hardcoded issue `859` and asserted `run_cmd.py 859` resolved to the current
checkout. Green in my worktree, so it merged. The moment #859 *closed*, `pmtools
close` tore that worktree down — and now `run_cmd.py 859` matched nothing, the
assertion went `1 == 0`, and the **whole suite went red on `main` and every other
worktree**. Since the close-gate runs the full suite, that blocked every close in
the fleet. I only saw it when I claimed the *next* ticket (#892) and ran the suite
after claiming.

**What I learned:** A test that passes only from the worktree it was written on is a
time-bomb: it's green for the author and goes red for everyone else the instant that
ephemeral worktree disappears. The whole-suite close-gate turns that from "one
agent's problem" into "nobody can close." The fix (#895) was to derive the
`(path, issue)` fixture from the live `git worktree list` at runtime — prefer the
current checkout if it's itself an issue worktree, else any other live worktree,
else `pytest.skip`.

**The rule:** **Never bake the authoring worktree's identity (issue #, path) into a
test — derive worktree/issue fixtures from runtime `git worktree list`, or skip.**
(Authority: #895; its closing comment records the rule.)

---

## 3. Run the full suite right after claiming — the base may be red through no fault of yours

**What happened:** The #895 red wasn't visible on the ticket I was starting (#892) —
it surfaced only because I ran `make test` immediately after claiming and entering
the worktree. A fresh worktree branches from `origin/main`, so it inherits
whatever red another agent (or a past-me) merged.

**What I learned:** "I just claimed, the branch is clean, so it's green" is an
assumption, not a fact. The post-claim suite run is what converts it to a fact —
and here it caught a fleet-wide blocker before I'd written a line of the actual
ticket.

**The rule:** **Run the full suite right after claim/merge; a green diff on a red
base is still red. Fix `main` first.** (Authority: existing fleet convention; see
the "fleet merge race" agent memory.)

---

## 4. Surface a self-introduced blocker — and route it to its own ticket

**What happened:** Finding #895's red mid-#892, I had two choices: fold the one-line
test fix into the #892 docs branch (fast, but bundles an unrelated bugfix into a
docs ticket and leaves `main` red until #892 closes), or stop, file a `severity:high`
bug, and fix it in its own worktree first. I surfaced the finding to the human with
both options and my recommendation rather than deciding unilaterally — the human
chose the separate ticket. I fixed #895, confirmed `main` green from a clean
checkout with the worktree torn down (the exact prior red condition), then rebased
#892 onto green `main` (`git merge origin/main`) and finished it.

**What I learned:** A blocker I introduced is still new work, and "one deliverable
per issue" doesn't bend just because *I'm* the one who broke it. Routing the fix to
its own ticket kept the docs change clean, gave the regression a real red-without-fix
guard, and got `main` green fastest via a focused hotfix. Surfacing the fork instead
of picking one on my own kept the human in the decision that was theirs.

**The rule:** **A blocker you introduced still gets its own ticket + regression test;
surface the fork with a recommendation, don't fold it in and don't decide it
alone.** (Authority: CLAUDE.md "Suggest, don't act" + "one deliverable per issue".)

---

## 5. Sync-by-hand invites re-drift — guard it or it rots

**What happened:** #859 added `make run-cmd`; nobody updated the README, so its
"For contributors" list documented 5 of 7 targets while `make help` listed all 7 —
`run-cmd` and `goldens` were undocumented. #892 hand-synced them. But hand-syncing
is exactly what failed the first time, so I filed #896: a drift-guard test asserting
the README's `make <target>` set equals the Makefile's target set, red the moment a
new target is added without a README mention.

**What I learned:** Fixing a sync gap by re-syncing by hand fixes the instance, not
the class — the next added target drifts the same way. The pycats codebase already
knows this pattern (the `combat/provenance.py` ↔ `tests/test_tuning_provenance.py`
drift-guard); prose deserves the same treatment.

**The rule:** **After hand-syncing two sources of truth, file/​add the guard that
keeps them synced — a manual fix without a guard is a scheduled re-drift.**
(Authority: #896 filed to add the guard.)

---

## What landed

| Artifact | Change |
|---|---|
| `scripts/run_cmd.py`, `make run-cmd`, RULES.md | Worktree/branch/issue → `cd '<wt>' && make run` generator (#859) |
| `tests/test_run_cmd.py` | Rewrote the CLI test worktree-agnostic; unblocked the fleet close-gate (#895) |
| `README.md` | Synced dev-command docs to `make help` — added `run-cmd`, `goldens` (#892) |
| (filed) #896 | Drift-guard test: README target set == Makefile target set |

## Related artifacts

- Issues #859, #892, #895, #896
- Agent memory: `no-worktree-coupled-e2e-tests`, `fleet-merge-race-run-suite-early`
- Drift-guard precedent: `tests/test_tuning_provenance.py`
