# TIL 2026-06-29 — FIG

**Context:** A long fleet session spanning screens, docs, tracker, and combat work
— shipped #131, #17, #121, #122/#174 (ADR-0002), #176, #182, #179, #99, #29, and
filed #134/#168/#169/#178/#192/#195. The recurring theme wasn't any one feature; it
was *checking what already exists before acting*, and making sure each lesson and
each guessed value left a durable trail.

---

## 1. "Surface, don't duplicate" — half my tickets were already (partly) done

**What happened:** Four times I was handed work that already existed. #17 ("apply
'Cat Fight' to the start screen") was already rendered on `main`. A request to
"assess + improve code quality" was the closed architecture-review umbrella #56
with ~10 follow-ups already landed (incl. the #69 `Player` decomposition). "Make
sim magnitudes pixel-agnostic" was #80 — closed with an explicit *recommendation
against it*. And #16's skin selection is subsumed by epic #127. In each case the
reflex "the user asked, so file/implement" would have produced a duplicate or
re-litigated a settled decision.

**What I learned:** A user request is a *starting hypothesis about the work*, not a
description of the repo's current state. The cheap `gh issue list --state all`
keyword scan + reading the closed ticket's findings doc repeatedly changed the
answer from "do it" to "it's done — here's the artifact" or "it was decided the
other way." The deliverable for an already-done item is the *missing guard* (a
regression test, #17) or *surfacing the contradiction*, not the feature.

**The rule:** **Before filing or implementing a request, scan all-state issues +
existing docs for it; if it's done or decided, surface that (with the artifact)
instead of duplicating.** (Authority: RULES "Filing work" — a question isn't
authorization — and "Fixing bugs" — already-fixed → ship the missing test.)

---

## 2. A lesson only counts once it's in RULES, not the session narrative

**What happened:** I kept re-hitting the same friction (pmtools `close` exits 1
after a successful `CLOSE OK`; no-code tickets need `gh issue close` + `pmtools
release`; run the suite right after claiming). These were "known" — in memory and
TILs — yet still bit, because they weren't in `RULES.md`. The fix wasn't another
TIL; it was #182 (codify the four close-discipline points into RULES) and #179
(codify the defensive-read rule), each landing the rule where the next agent reads.

**What I learned:** `docs/learnings/` is a diary, not an authority. A rule that
lives only there expires when the session ends — exactly the pattern #29's tracker
was created to fix (the close protocol was wired into tooling but never documented).

**The rule:** **When a lesson is a reusable rule, land it in `RULES.md` (or file a
ticket to), in the same breath as the TIL — the narrative is the prompt, RULES is
the authority.** (Authority: this TIL's lessons trace to #182/#179, both merged.)

---

## 3. No-code tickets and decisions have their own close path

**What happened:** #122 and #174 were `decision` tickets; #29 was a tracker whose
children were all silently complete. None had a `Closes #N` commit, so `pmtools
close` (which needs one to land+verify) was the wrong tool. The right path: rule the
decision, **record it as an ADR** (`docs/adr/0002-dual-backend-endgame.md`), then
`gh issue close` + `pmtools release` to drop the claim/worktree. For the tracker:
reconcile the stale checkboxes against reality, then close.

**What I learned:** The fleet's `Closes #N` + `pmtools close` flow assumes *code*.
Decisions and trackers are real work with no diff — forcing a no-op commit to
satisfy the tool is the wrong instinct. And a decision isn't "done" until its
rationale is durable (an ADR), or it gets rediscovered the hard way.

**The rule:** **A decision/research/tracker ticket closes via `gh issue close` +
`pmtools release`, and a ruling isn't finished until it's an ADR.** (Authority:
RULES "Closing work" no-code path, landed in #182; ADR practice in
`docs/adr/0001-record-architecture-decisions.md`.)

---

## 4. When canon isn't look-up-able, guess *loudly* and leave a trail

**What happened:** #184 (PM-faithful air dodge) needs tuning magnitudes that simply
don't exist in pycats' units — SmashWiki gives Melee *mechanics* and some frame
data, but no Project-M air-dodge speed, and Melee engine units don't map to pycats'
pixel scale. Rather than bury a silent guess in a constant, I marked every value
FOUND-vs-GUESS in `GUESSED_VALUES_TO_RESEARCH.md` and filed umbrella #192 to replace
them. Then #120 (closed) turned out to already hold the *derivation path*: PM values
in units/frame × `PX_PER_UNIT ≈ 5.4` — so the guesses became *sourceable*, and I
filed #195 to make that constant explicit.

**What I learned:** A guess is fine; an *unmarked* guess is a future bug that reads
as fact. The discipline of writing the guess down with its status and a tracker
turned "I made up 14" into "here's the derivation and where to get the real number."

**The rule:** **A value you couldn't source gets a marked GUESS + a tracking ticket,
never a silent constant — and check whether a prior research ticket already gives
the derivation.** (Authority: tracked by #192; `GUESSED_VALUES_TO_RESEARCH.md`.)

---

## Open threads
- **#184** core implementation (momentum-replace + `helpless` leaf) is parked
  mid-claim with the values trail committed WIP on its branch; wavedash → file
  #184b. See `/tmp/handoff-fig-184-16.md`.
- **#16** recommended for close-as-superseded-by-#127 (awaiting go-ahead).

## Related artifacts
- ADRs: `docs/adr/0002-dual-backend-endgame.md`
- Docs: `CONTEXT.md`, `docs/project-m-parity.md`, `GUESSED_VALUES_TO_RESEARCH.md`
- Sibling TILs: [DRAGONFRUIT](./today-i-learned-2026-06-29-dragonfruit.md), [CHERRY](./today-i-learned-2026-06-29-cherry.md)
