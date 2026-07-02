# TIL 2026-07-01 — GRAPE

**Context:** A long fleet session. Picked up the #342 input-port split (from a handoff), then the whole B-a/S5 provenance arc under #264: reviewed #319/#226, walked the human through accepting ADR-0003 (`guide-human-decision`), built the tuning-provenance registry + drift-guard (#233), scoped #319 as a spike and landed its value-sourcing buckets A/B/C (#378/#382/#384). Then a big gameplay feature — true PM edge-hog (#311) — through a rough fleet merge race. Several orchestration + issue-review rounds. Finished by **reverting** a feature I'd just shipped (#405 input overlay) because it re-invented an existing component, filing the follow-ups (#434/#435), and setting up the ⚠/🔬/❓ marker legend (#408).

---

## 1. `pmtools close` REBASES — merge-commits + regenerated goldens re-conflict every attempt

**What happened:** #311 was a long slice; while I worked, `origin/main` advanced three times (font-scale, the `run`→`walk` rename #388, options-menu #389), each regenerating goldens. My branch also regenerated the ledge goldens. `pmtools close 311` kept aborting: `✗ rebase hit a real conflict in tests/golden/*.json`. I had been *merging* `origin/main` into my branch to stay current — which made it worse: the merge commits just got replayed on `close`'s rebase and re-conflicted on the goldens every time. Four failed closes before I understood it.

**What I learned:** `pmtools close` **rebases** the branch onto `origin/main`, not merges. So a branch with merge commits + generated-file (golden) changes will re-conflict on every close attempt, because both sides regenerated the same `.json`. Merging `origin/main` in doesn't help — it adds history to replay. The fix is to present `close` a *linear* branch whose goldens are already based on the current tip.

**The rule:** **When a long slice regenerates goldens and `origin/main` moved, collapse to one clean commit on the current tip before closing: `git fetch origin main` → `git reset --soft origin/main` → regenerate goldens fresh (review the summary sidecars) → single `git commit` with `Closes #N` → `pmtools close`.** A single commit whose goldens sit on the current tip rebases as a no-op. (Codified in the `fleet-merge-race` memory pin; extends the "run suite early" lesson.)

---

## 2. Confirm a "we already have X / this re-invents Y" claim by grepping — *before* reverting merged, tested code

**What happened:** After I shipped #405 (an on-screen input overlay for watch playback — held keys as arrows + button words), the ask came to revert it: it "re-invents the move/key input-buffer display we already have." Reverting green, merged, tested code on a mistaken premise would be a real mistake, so I grepped first: `grep -rniE "input.?buffer|input.?history|input.?display" pycats/`. It confirmed the premise — **#21's `InputHistory`** exists (`pycats/input_history.py`: last-10 press-edge inputs in Project M notation like `↑A`, TTL-expiring, rendered by `render_battle.draw_input_history`, wired into the live game). My #405 was a *parallel, lesser* re-implementation. Revert justified.

**What I learned:** The revert instruction was correct — but I only knew that *because* I verified. "This duplicates X" is a hypothesis; the target is merged code, so the cost of being wrong is high. Also learned the mechanics: a revert has to land through `pmtools`, which needs a `Closes #N` — so the undo needs **its own closeable ticket** (#435), separate from the forward-looking "do it right" follow-up (#434). Two tickets, not one.

**The rule:** **Before reverting merged code because it "duplicates" something, grep for the thing it supposedly duplicates and read it — confirm the premise. Then land the revert via its own closeable ticket (`git revert <sha>` → `Closes #<revert-ticket>`), and file the correct-approach work as a separate open follow-up.** (Extends the defensive-read rule to the revert case.)

---

## 3. A DEV ticket that says "scope/confirm in the ticket" isn't build-ready — resolve the design forks *in the ticket*

**What happened:** `/issue-review-skill` on #405 (before I implemented it) scored 13/15 — it had great file-anchor grounding but **no acceptance criteria** and three unresolved "Open questions (for the spike/scope)" plus a "Mechanism (sketch)". The user asked me to rewrite it first: I added machine-verifiable acceptance + a test oracle and *resolved* the three open questions (visual form, held-vs-pressed, opt-in) into decisions, then implemented to that spec. Reviewing #413 the same day showed the mature pattern: its owner had appended a **"Design updates — LOCKED"** section fixing edge-hog/edge-guard precedence + level thresholds, so it scored 15/15.

**What I learned:** A ticket that defers its own design decisions to "the spike" is not implementable without inventing those decisions mid-flight — which is exactly the architect-in-courier-mode trap. The review's real value isn't the score; it's catching the undecided fork and forcing it into the ticket body *before* code.

**The rule:** **Before claiming a DEV ticket, resolve or explicitly delegate its open design questions in the ticket (a "LOCKED decisions" block) and give it machine-verifiable acceptance — an unresolved fork is a NEEDS-WORK even at 13/15.**

---

## 4. The orchestration snapshot decays fast — re-validate availability at claim time, not from the assignment

**What happened:** I ran `/fruit-agent-orchestrate` and assigned myself #413. Minutes later, asked to validate #413 for pickup, I checked `pmtools status --json` — its `claims` array now contained **413**: another agent had claimed it between the snapshot and now. The assignment "GRAPE: take #413" was already stale. Same session: `#404` (edge-hog slice 1) went from unclaimed → closed while I was mid-task; `#336`/`#405` availability shifted round to round.

**What I learned:** In an active fleet the open-issue snapshot the orchestrator freezes into prose is decaying the instant it's written — exactly the freshness contract the skill warns about. The authoritative in-flight signal is the origin `refs/claims/*` (`status --json` `claims`), which is cross-clone-safe; `git worktree list` only sees the local clone.

**The rule:** **Never claim from an orchestration snapshot without re-checking the ticket's live state + the `claims` array right before claiming — a ticket assigned minutes ago may already be in-flight elsewhere.**

---

## 5. Hand feel-changing design forks back to the human — don't silently bake gameplay decisions

**What happened:** #311 (edge-hog) had two forks the ticket didn't fully pin: on a mistimed hog, does the incoming grab *evict* the occupant or just get denied? And does adding a getup climb-window change the currently-instant getup (and its test)? Both change game *feel*, not just implementation. Rather than pick, I used `AskUserQuestion` to surface each as an option with a recommendation — the human chose evict + windowed getup, and I built to that.

**What I learned:** Golden-safety and tests can't adjudicate a feel decision — "should a mistimed hog lose the ledge?" is a design call the human owns. Surfacing it as a 30-second choice (with a recommendation) is cheaper than building the wrong feel and reverting, which is exactly what happened with #405 when I *didn't* stop to confirm the approach.

**The rule:** **When an implementation fork changes game feel (not just internals), stop and put it to the human as a choice with a recommendation — don't let the code silently decide gameplay.**

---

## 6. A semantic golden-summary shift is a prompt to trace to ground truth — and it can expose a real follow-up

**What happened:** #311's `full_match` golden summary moved: battle 812→910f, P2 `percent_max` 40→**190**. Counterintuitive — shorter ledge invincibility should make recovery *less* safe, not let P2 survive to higher percent. Instead of regenerating, I traced it: P2 is the idle dummy; once its (now short) invincibility burst lapses it's *vulnerable* on the ledge, so P1 chips it — but the #14 hang **pins position** (`vel=0` each frame), so the chip damage never knocks it off until timeout. Same *outcome* (P1 wins, P2 loses all stocks), explainable arc. And it surfaced a genuine gap: a hit on a vulnerable hanger should knock them off — filed as #400 (deferred, post-V1).

**What I learned:** A surprising golden delta is a lead, not a nuisance to regen away. Tracing it either confirms the change is legit (semantics preserved, positions shifted) or finds a real bug — here it did both, exposing a pre-existing pin-absorbs-knockback gap that #311 made visible.

**The rule:** **When a golden's *semantic summary* (not just raw positions) shifts, trace it to ground truth before regenerating; a counterintuitive shift often exposes a real follow-up worth filing.**

---

## 7. An "unresolved-items" guard must derive its expectation independently, or it can never fail

**What happened:** Building the #233 drift-guard, I first wrote `TUNING_CONSTANT_NAMES = frozenset(TUNING_PROVENANCE)` — deriving the "expected names" set from the registry's own keys. The "no orphans" test then asserted `set(TUNING_PROVENANCE) == TUNING_CONSTANT_NAMES` — which is `X == X`, a tautology that can **never** go red. Caught it before committing and made `TUNING_CONSTANT_NAMES` an **independent hand-maintained literal**, so adding a constant to one but not the other reds the test. Revert-checked all three drift-guard assertions (flip a value / drop a name / rot a derivation) to prove each can fail.

**What I learned:** A guard that computes both sides of its own equality from the same source is a Liar test. The whole point of "no orphans" is to catch a human forgetting one side — which only works if the two sides have independent origins.

**The rule:** **A completeness/"no orphans" guard must compare against an independently-authored expectation, never one derived from the thing under test — and prove it able-to-fail before trusting it.**

---

## What landed

| Artifact | Change |
|---|---|
| `pycats/input_poll.py` | Split `poll()` out of the rules core (#342) |
| `pycats/combat/provenance.py` + `tests/test_tuning_provenance.py` | ADR-0003 tuning-provenance registry + drift-guard (#233); value-sourcing A/B/C (#378/#382/#384) |
| `docs/adr/0003-*.md` | Proposed → Accepted via `guide-human-decision` |
| `pycats/entities/{ledge,player,fighter}.py`, `charts/fighter_chart.py` | True PM edge-hog: percent-scaled invincibility + hog timing + half-anim regrab (#311) |
| `pycats/sim/presenters.py` (reverted) | #405 input overlay — shipped then **reverted** (#435) as a re-invention of #21 |

## Open threads

- #434 — reuse #21's `InputHistory`/`draw_input_history` in the watch presenters (the correct #405).
- #400 — a hit on a vulnerable ledge-hanger should knock them off (post-V1; the #311-exposed pin gap).
- #408 — ⚠/🔬/❓ marker legend, blocked on #410 (magic-number audit) so we don't mark magic numbers + labels + markers at once.

## Related artifacts

- [TIL 2026-06-30 GRAPE](./today-i-learned-2026-06-30-grape.md) — the prior review-before-claim / byte-identical-oracle / ADR-first session this builds on.
- `fleet-merge-race` memory pin — the `pmtools close` rebase sub-case (lesson 1).
