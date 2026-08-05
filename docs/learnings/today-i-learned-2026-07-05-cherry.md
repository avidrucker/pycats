# TIL 2026-07-05 — CHERRY

**Context:** A long tooling-and-tracker session: finished the ruff rule-expansion epic
(#524 UP pyupgrade + Python-3.10 floor, #525 `ruff format` adoption, closed epic #505/#492),
built the ICE scoring system (#449), codified the "no unprompted research" rule (#220),
implemented watch/demo input display by reusing #21 (#434), researched PM smash-input
naming (#436), and reconciled three requested control-architecture tickets against an
existing epic (#553/#554/#555 vs #476/#156).

---

## 1. Ground subjective scores in an existing rubric — don't fabricate them

**What happened:** #449 asked me to backfill ICE scores (Impact × Confidence × Ease) for
~40 issues. The spec (#199) was emphatic it must be a *considered* pass, not a label
auto-sweep. My instinct was to just start assigning numbers — but 40 subjective Impact
calls about someone else's game priorities is exactly the kind of thing the human should
own or review. The user's answer: use `/issue-review-skill` per issue to *ground* the
scores. That dissolved the problem. The issue-review readiness **verdict maps straight to
Confidence** (READY=1.0 / NEEDS WORK=0.8 / BLOCK=0.5); **single-deliverable + file-specificity
+ scope map to Ease**; only **Impact** stays a genuine judgment call — so I flagged that one
axis for the human and reserved it for review. The CSV is git-tracked, so the diff *is* the
review gate (#199 §2 designed it that way).

**What I learned:** When a task needs many subjective numbers, the win isn't "assign them
carefully" — it's finding an existing, principled rubric that *derives* most of them, so the
only thing left is the one axis a human must own. Two of ICE's three axes fell out of the
issue-review rubric for free.

**The rule:** **Before hand-assigning subjective scores, map them onto an existing rubric; derive what you can, and reserve only the genuinely-human axis for review via the diff.**

---

## 2. Rounding a sort key erases its tiebreak

**What happened:** The ICE formula has a tiebreak: `ICE = I×C×E + 1/(issue×1000)` so earlier
issues win ties (FIFO). I stored `ice_score` rounded to 5 decimals and sorted by it. But
`1/(220×1000) = 0.0000045`, which **rounds away at 5 decimals** for any 3-digit issue number —
so the tiebreak vanished and ties fell to arbitrary batch order. My validation flagged "44
mismatches" which looked alarming but was just the rounding.

**What I learned:** A tiebreak baked into a floating-point score only survives if the stored
precision is finer than the tiebreak's magnitude. Cleaner to separate concerns: store the
*clean* displayed value (`ice_score = I×C×E`, e.g. `10.0`) and compute the rank by sorting on
`(-ice_score, issue_number)` — the tiebreak lives in the sort key, not smuggled into a rounded
column. After the fix, #434 and #477 (both 10.0) ranked by issue number as intended.

**The rule:** **Don't smuggle a tiebreak into a rounded score column — round the display value for humans and break ties explicitly in the sort key.**

---

## 3. A safe fix that removes exactly the dead names beats an unsafe fix

**What happened:** #524's UP pyupgrade sweep. `ruff --select UP --fix` converted `List[X]`→
`list[X]` (UP006) but left 11 `typing.List/Tuple/Dict` imports flagged UP035, whose fix is
`[-]` *unsafe*. The tempting move was `--unsafe-fixes`. Instead I checked: after the UP006
conversion those imports were now genuinely unused (F401 confirmed; the only textual "List"
left was a docstring word `"platforms: List of all platforms"`). So I removed them with the
**safe** F401 fix — which deletes exactly the dead names and keeps the used ones (`Protocol`,
`Any`) — rather than the blunt UP035 unsafe rewrite.

**What I learned:** An "unsafe fix" label often means "the tool can't prove this is safe" —
not "this is unsafe." Frequently a *different, safe* rule targets the same end state once you
establish the precondition the unsafe fix couldn't. Verify the precondition (here: the import
is annotation-only), then reach for the safe tool.

**The rule:** **When a fix is flagged unsafe, look for a safe rule that reaches the same result once you've verified the precondition the tool couldn't prove.**

---

## 4. Reconcile a requested *set* against the tracker before filing any of it

**What happened:** The user asked me to file three control-architecture research tickets. Before
filing, I searched — and found an **open epic #476** ("PM input-handling parity") whose stated
threads 2 and 3 already *were* two of the three requests near-verbatim, plus a **closed #156**
that already did the GameCube-vs-keyboard feasibility. Filing three fresh tickets would have
duplicated the epic and violated its "one thread at a time" discipline. So I surfaced the overlap,
proposed fitting the catalogue in as #476's thread 2, and only filed the two genuinely-new pieces
standalone. To capture the catalogue now without breaking the epic's sequencing rule, I used the
`Sequenced after: #477` body convention — filed today, but not worked until thread 1 closes.

**What I learned:** "File these N tickets" deserves a dedup pass *as a set*, not per-ticket. The
existing tracker often already owns part of the request under a different name; the value is fitting
the new intent into the existing structure, not minting parallel tickets. And when an epic's
discipline (file one at a time) collides with "capture it now," `Sequenced after: #N` resolves the
tension — capture without working.

**The rule:** **Before filing a requested set of tickets, search for an epic that already owns part of it; fit the intent in and file only the genuinely-new remainder — use `Sequenced after: #N` to capture-without-working when an epic's sequencing would otherwise block it.**

---

## 5. When a protocol gains a parameter, its test doubles must conform

**What happened:** #434 threaded `inputs=fi` from the runner into `presenter.show(...)` — the
runner→presenter protocol gained an `inputs=None` parameter. The full suite then went red in 9
places: three **test-double presenters** (`_NullPresenter`, spy presenters) whose `show()` still
had the old signature, plus a `__new__`-built partial `LivePresenter` in a test helper missing the
new `show_inputs` attribute. Updating them to accept `inputs=None` / set the new attribute is not
weakening the tests — it's conforming the doubles to the real protocol every real presenter now
implements.

**What I learned:** A signature change to a widely-implemented interface has a blast radius that
includes every fake, stub, and partially-constructed instance in the test suite. Those failures
aren't "the change broke tests" — they're "the doubles are stale." Grep `def show(` across `pycats/`
*and* `tests/` before assuming the change is done.

**The rule:** **When you add a parameter to an implemented protocol, grep the test tree for its doubles and conform them — a stale fake failing is the protocol change working.**

---

## 6. Close from main, not from inside the worktree (pmtools#104)

**What happened:** Earlier sessions taught "`pmtools close` exits 1 after success (cwd deleted) —
trust the banner." This session the worktree CLAUDE.md carried an update: pmtools#104 makes `close`
resolve the worktree by issue number, so running it **from the main checkout** exits **0** and leaves
your shell where it is; running it from *inside* the worktree still works but exits 1 and strands the
shell. I closed #524/#525 from the worktree (exit 1, as expected) and #449/#220/#434/#436 from main
(exit 0, clean). Both work; from-main is the cleaner path.

**What I learned:** The tooling evolved past a quirk I had memorized. The worktree's own CLAUDE.md is
the live source for close mechanics — re-read it rather than acting on remembered behavior.

**The rule:** **Run `pmtools close <N>` from the main checkout (exit 0, comment in place), not from inside the worktree (exit 1, strands the shell) — pmtools#104.**

---

## What landed

| Artifact | Change |
|---|---|
| `ruff.toml`, `.pre-commit-config.yaml` | UP + `target-version=py310` (#524); `ruff format --check` hook (#525) |
| whole `pycats/` tree | one-time `ruff format` — 64/78 files (#525); closed epic #505/#492 |
| `stats/ice-scores.csv`, `.claude/orchestrate.json` | ICE ranking spine + `advisory.iceSource` (#449) |
| `RULES.md`, `CLAUDE.md` | "No unprompted research" rule (#220) |
| `pycats/sim/presenters.py`, `runner.py`, `watch.py` | `--show-inputs`: reuse #21 InputHistory in watch (#434) |
| `docs/research/pm-tap-smash-input-naming-findings.md` | PM smash-input naming (#436) |
| #553 / #554 / #555 | control-architecture ticket set (catalogue / keyboard-scope decision / N-controller spike) |
| #540 | follow-up: extend ruff coverage to root scripts |

## Related artifacts

- Issues #524 #525 #449 #220 #434 #436 #476 #553 #554 #555
- Rule authority: #220 codified in `RULES.md` + `CLAUDE.md`; pmtools#104 close mechanics in `CLAUDE.md`
