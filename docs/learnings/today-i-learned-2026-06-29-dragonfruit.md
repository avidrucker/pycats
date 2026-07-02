# TIL 2026-06-29 — DRAGONFRUIT

**Context:** A combat-and-tracker-lane session: air-dodge research (#23 → filed #184),
a TDD crouch-cancel DEV (#135), CPU-difficulty research (#148), a codebase-wide
Project M parity audit run by parallel subagents (#189 → correction #194), and a
banned-words frequency study (#191). Plus an orchestration round (the #185
initiatives map). The through-line: **what a finding is worth before you act on it.**

---

## 1. A delegated finding is a lead, not a fact — verify it in code before filing

**What happened:** I ran #189 (a parity progress report over the whole codebase) by
fanning out six subagents, one per subsystem, each returning a `✅/🟡/⬜` table. The
report surfaced two crisp-looking "follow-up bugs," and when asked to "file the 2
tickets," I almost did. Instead I opened the named `file:func` first. Both were wrong:
the `StatechartScreenEngine` an auditor called *"nothing wires it into the live game"*
is in fact wired behind `make_screen_engine(backend=os.environ.get("PYCATS_SCREEN_BACKEND",
"legacy"))` (`screen_manager.py:97`) — `PYCATS_SCREEN_BACKEND=statechart` runs the
whole live flow on it; legacy is just the default. And the Nalio d-tilt an auditor said
*"down+A doesn't resolve"* **does** play, via the documented `"attack"` fallback in
`resolve_move_key` (`move_select.py:58`). Filing them would have duplicated #100/#142
and committed two false claims to the tracker.

**What I learned:** A subagent's table cell carries the *authority of prose* without
the *verification of code* — it reads like fact but is one model's read of a few files
under time pressure. The parallel sweep is excellent for coverage and terrible as a
source of truth for any single actionable claim. The fan-out also drifted on the HEAD
sha (main advanced mid-run), another reminder the snapshot is soft.

**The rule:** **Before filing or acting on a delegated/audit finding, open the named
`file:func` and confirm it — a subagent's report is a lead to verify, not a fact to
file.** (Added to RULES.md → *Filing work*, same commit.)

---

## 2. Surface the contradiction; hand the decision back — don't comply or silently drop

**What happened:** Once verification showed both #189 follow-ups were already tracked
(d-tilt → #142, screen-backend flip → #100), the instruction "file the 2 tickets" no
longer fit reality. I didn't file them, and I didn't quietly skip them either — I
reported the contradiction and offered options. The chosen path: annotate the two
owning epics, and file one small ticket (#194) to *correct the report's own wrong rows*.

**What I learned:** "File X" is a means to an end; when the premise is false, executing
it literally is the wrong service. Filing is outward-facing and costly to unwind, so a
contradiction is exactly the moment to stop and put the call back to the human. Fixing
my *own* just-landed report (#194) is part of owning the deliverable, not a detour.

**The rule:** **When an instruction's premise turns out false on verification, surface
it and return the decision — never execute an outward-facing action on a premise you've
just disproven.** (Corollary of the existing "surface the contradiction before an
outward-facing close" rule.)

---

## 3. Research-ticket premises go stale — reconcile against current `main` first

**What happened:** Two research tickets opened on premises the repo had already moved
past. #23 asked whether air-dodge *cancelling vertical momentum* is intended — but on
current `main` the code *preserves* Y (it never zeroes it); the premise was stale. #148
described the CPU controllers as *"RNG-free"* and treated a graded difficulty ladder as
impossible without RNG — but #166's seeded-RNG seam had since landed, making it
golden-safe. In both cases the most useful first move was checking what the code does
*now*, not answering the ticket as written.

**What I learned:** A ticket body is a snapshot from its filing date; in a fast fleet it
decays the same way an orchestration plan does. The finding is often "the premise is
stale" — and that *is* the deliverable, not a failure to answer.

**The rule:** **Open a research ticket by reconciling its premise against current
`main`; the honest answer is sometimes "this no longer reproduces / no longer holds."**
(Sibling of the reconcile-before-filing rule.)

---

## 4. Parallel per-subsystem auditors: great for coverage, needs a verify gate

**What happened:** #189 covered ~95 mechanics across combat/moveset/movement/fighters/
AI/screens by dispatching one general-purpose auditor per subsystem with a tight brief
(read these files, cross-ref this oracle doc, return a grounded table with `file:func`
evidence + confidence), then synthesising. Six agents finished in ~80s each; I kept the
conclusions, not the file dumps.

**What I learned:** The pattern scales a read-heavy audit well *and* its weakness is
exactly Lesson 1 — independent agents will each produce a plausible-but-unverified
claim or two. The synthesis layer (me) is where accuracy has to be enforced, so any row
that becomes an *action* gets a verify pass; rows that stay descriptive can ride.

**The rule:** **Fan out read-only auditors for breadth, but treat their output as a
draft to verify at the synthesis step — never let a subagent cell become a filed ticket
unchecked.**

---

## 5. Mechanics I re-confirmed (quick hits)

- **TDD crouch-cancel (#135):** scaled `kb *= CROUCH_CANCEL_FACTOR` (0.67) in
  `Fighter.receive_hit` gated on `state=="crouch"`. The can-fail proof was clean —
  constant-only first (crouch == standing launch, RED) → add the scaling (GREEN). The
  golden never crouches, so the sim oracle is untouched (433 passed). [[fleet-merge-race-run-suite-early]]
- **No-code ticket close (#191):** a comment-only research deliverable has no `Closes #N`
  commit, so `pmtools close` has nothing to scan — close it with `gh issue close` +
  `pmtools release` (drops the claim ref + worktree, issue stays closed).
  [[pmtools-release-for-nocode-tickets]]
- **Frequency before taste (#191):** the canonical "AI tells" (delve/tapestry/seamless)
  barely appear in this repo (~1 each); the real over-use is the quiet set (leverage 12,
  simply 14, robust/robustness 23) — and a chunk entered via *recent agent-written
  docs*. Scan the corpus before assuming which clichés matter here, and carve out the
  words with a real technical sense (`key`, `harness`, `clean hit`).

---

## What landed

| Artifact | Change |
|---|---|
| `docs/research/air-dodge-vertical-momentum-findings.md` | #23 findings; air dodge is Brawl-style, PM is Melee-style → filed #184 |
| `pycats/combat`/`entities/fighter.py` + `tests/test_crouch_cancel.py` | #135 crouch-cancel 0.67× + able-to-fail regression test |
| `docs/research/2026-06-29-pm-cpu-difficulty-levels-1-9.md` | #148 deterministic Lv 1/3/5/7/9 mapping; #166 seam resolves #48's RNG-free tension |
| `docs/current-parity-progress-report.md` | #189 codebase-wide parity report (6 parallel auditors) + #194 correction |
| #191 comment | banned-words candidate table + ~10-word shortlist |
| `RULES.md` (this commit) | verify-delegated-findings-before-filing bullet |

## Open threads

- The #191 shortlist awaits a human pick → a follow-up DEV ticket edits `banned_words.md`.
- #194's two corrected rows are tracked on their epics (#142 d-tilt re-key, #100 slice-4
  backend flip) — neither is a standalone ticket.

## Related artifacts

- Issues #23, #135, #148, #189, #194, #191, #184, #185
- Prior DRAGONFRUIT TIL: [2026-06-28](./today-i-learned-2026-06-28-dragonfruit.md) — the
  reconcile-before-filing + no-code-close threads continue here.
