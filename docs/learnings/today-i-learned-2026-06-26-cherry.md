# TIL 2026-06-26 — CHERRY

**Context:** A long PM-heavy session that started with `/fruit-agent-orchestrate`
rounds and turned into hands-on work: applying the `area:*` label taxonomy
(#91/#93), reconciling the 64 free-form `#### TODO:` source comments against the
tracker (#50), filing the icebox proposal (#104) and the first cleanup batch
(#106) + an `xfail` guard (#112), and finally taking the two bug tickets the
reconciliation surfaced (#101 thick-platform passthrough, #102 stuck-red HURT
tint) — both of which closed **non-repro** with a regression guard.

---

## 1. In fleet work, the tracker moves under you — re-validate before every claim and edit

**What happened:** Three live races in one session. (a) Between two
`/fruit-agent-orchestrate` rounds, DRAGONFRUIT closed #86 and spawned #92/#97/#98/#99
— my round-1 assignment list was stale within the hour. (b) Mid-edit on the #50
cleanup, `fighter.py:256/257` had silently shifted to lines 271/272 because a
concurrent agent implemented respawn-invulnerability — a line-number delete would
have removed *real code* (`self.invulnerable_timer = 0`), not the comment I meant.
(c) While I was *studying* the collision code to write #101's repro test, another
agent closed #101 out from under me; `pmtools claim 101` correctly refused with
`#101 is CLOSED -- nothing to claim`.

**What I learned:** "OPEN a moment ago" is not "OPEN now." The orchestrator's
freshness contract (the `## ⏱ Triaged as of …` banner, #1159) isn't ceremony — the
snapshot genuinely decays mid-task. Two concrete defenses paid off repeatedly:
`git fetch` + re-grep *by content* right before editing, and trusting the
`pmtools claim` CLOSED-guard as the backstop against cross-clone work I can't see in
my own `git worktree list`.

**The rule:** **Re-fetch and re-locate by content (never by stale line number)
immediately before each edit/claim; let the claim's CLOSED-guard, not your
memory, decide if a ticket is still yours.**

---

## 2. A reconciliation document is not work — tool-tracked markers are

**What happened:** #50 began as "maintain a classification of the 64 source
TODOs." I found the *previous* session's inventory already stale — it was written
against the pre-D1 flat layout (`pycats/player.py` 40, …, total 73) and every
`file:line` ref had broken when the code moved into `entities/`/`core/`/`systems/`
(now 64, then 55). I refreshed it… and then realized I'd just produced a *second*
perishable artifact of the same kind. A `/yegor-pm` pass made the verdict explicit:
the document closes nothing and rots on the next refactor.

**What I learned:** The durable fix is to move the source-of-truth *into the code
and the tooling*: convert real deferred work to canonical `@todo #N` puzzles
(`pdd` is already enabled here — `pmtools status` even warned "no `.pddignore`"),
park aspirational features in one icebox (#104), delete the already-shipped ones
(#106), and encode the "→ 0" goal as a **failing test** (#112, `xfail(strict=True)`)
so completion is self-signaling. Velocity came from the delete-batch and the
guards, not from the classification.

**The rule:** **Don't hand-maintain a side-document for state the code and its
tooling can hold; if a "report" rots on a refactor, it was never the deliverable.**

---

## 3. A repro ticket's deliverable is a failing test — and "doesn't reproduce" still ships a guard

**What happened:** #101 and #102 were already "Research: reproduce & spec"
tickets. The user proposed opening *two more* research tickets to block them and
"just reproduce the bugs." `/yegor-pm` flagged that as repro-blocking-repro —
duplicate work — so instead I scoped #101/#102 *down* to pure reproduction. Both
turned out **non-repro on current `main`**: #101's side/underside faces are handled
by `physics.solve_horizontal`/`solve_vertical` (the source TODO predated them), and
#102's "stuck red" premise was mooted by the #75 render-time refactor —
`render_battle.body_tint` derives RED from `hurt_timer`, and `Player.update`'s
decrement is *unconditional*. For each, the deliverable became the missing
regression test on the previously-uncovered face (thick-platform underside;
hurt-tint-while-moving/attacking), proven can-fail by reverting the fix.

**What I learned:** The two-step pipeline is **research(repro) → DEV**, not three
steps; a repro *is* the spike. And a non-reproducing bug is not a no-op close — per
RULES.md → "Already-fixed / non-reproducing bug?", the deliverable is the can-fail
guard that locks in the existing fix, plus surfacing the contradiction. The most
satisfying confirmation: the bug I *injected* for #102's revert-check (gating the
decrement on `state != "attack" and not held`) was literally the original symptom —
which is exactly why current `main`, lacking that gate, is already correct.

**The rule:** **Scope a repro ticket to one failing test; if it won't reproduce,
ship the regression guard for the uncovered case rather than closing empty.**

---

## 4. Fold, don't multiply — a new ticket needs genuinely-new, unowned work

**What happened:** The #50 reconciliation could have spawned 64 tickets. It
produced **two** (#101/#102 — genuinely-untracked bugs) plus one consolidated
icebox (#104); everything else folded into issues that already owned it (#38, #24,
#12–#14, #16, #11/#98) or was deleted. Likewise, when I wanted a CI-style guard for
#50, the instinct to "just file the test ticket" was right *because the test is
real work* (#112) — but I checked first that it wasn't already owned. And the
`area:*` taxonomy work (#91/#93) codified **one area label per issue** so the
orchestrator's lane gate actually partitions.

**What I learned:** "It's related to X" is a reason to *fold into X*, not to open a
new ticket. A new ticket is justified only by work that is both new and unowned —
otherwise it's the pile-of-bookmarks anti-pattern.

**The rule:** **Default to folding into the owning issue; open a new ticket only
for genuinely-new, unowned work — and give every ticket exactly one `area:*`
label** (now in RULES.md → "Labels & priority", #93).

---

## 5. Fleet identity doesn't survive worktree teardown

**What happened:** Asked who completed #101, I couldn't tell. The close commit is
authored by the shared `avidrucker` identity (all agents commit as that), and the
fruit name lived only in the branch/worktree (`br-<fruit>/…`), which `pmtools close`
deletes. It ran in a clone I can't see, so even by elimination I could only narrow
it, not name it.

**What I learned:** Post-hoc "which agent did this?" is currently unanswerable from
git alone once a worktree is torn down — a real traceability gap in the fleet model.

**The rule:** **If you want per-agent attribution to survive a close, stamp the
fruit into the commit (e.g. a `Worked-by: <fruit>` trailer) — the branch name won't
be there to ask later.**

---

## What landed

| Artifact | Change |
|---|---|
| `RULES.md` + `CLAUDE.md` | `area:*` convention + "question ≠ authorization" rule (#93/#91/#78) |
| 6 `area:*` labels | created + applied to every open issue (#91) |
| `#50` | re-shaped to the PDD-migration goal; perishable inventory demoted to a one-time spike |
| `tests/test_thick_platform_underside.py` | #101 underside regression guard (closed by a concurrent agent) |
| `tests/test_hurt_tint_clears_when_moving_or_attacking.py` | #102 regression guard, revert-check proven (`f8ecb73`) |
| `.pddignore` + 8 TODO deletions | first #50 cleanup batch (#106) |

## Open threads

- **Delete-by-content vs delete-by-line** deserves to be an explicit rule somewhere
  durable (candidate RULES.md addition) — it prevented a real code-deleting mistake
  this session but currently lives only here.
- **`Worked-by: <fruit>` commit trailer** (Lesson 5) — a small fleet-tooling change
  in `pmtools claim`/`close` would close the attribution gap. Not yet ticketed.
- **`pdd`/`0pdd` in CI** — deferred infra to auto-generate issues from `@todo #N`
  and reject un-issued markers; the cheap half (`.pddignore`) shipped, the enforcing
  half didn't.

## Related artifacts

- Issues #50, #91, #93, #101, #102, #104, #106, #112
- [TIL 2026-06-24 CHERRY](./today-i-learned-2026-06-24-cherry.md) — "reproduce to ground truth; fix the state not the adjective" (#9 "red") — directly foreshadows #102
- [TIL 2026-06-23 DRAGONFRUIT](./today-i-learned-2026-06-23-dragonfruit.md) — non-reproducing bug = missing test; prove a guard by reverting the fix; `pmtools close` exits 1 after success
