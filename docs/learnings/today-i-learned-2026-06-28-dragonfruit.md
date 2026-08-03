# TIL 2026-06-28 — DRAGONFRUIT

**Context:** A display/sim/research session: shipped the whole-cat tint consolidation (#109), the pure-ASCII profile/3-4 face heads retiring kaomoji+emoji (#114), and the `watch.py --vs` 30s/KO cap (#61); then filed + researched two Project M questions — same-time trade resolution (#141) and a randomness survey (#144). The most useful lessons came from a question I answered *wrong* first, and from a near-miss filing a spike for a bug that was already fixed.

---

## 1. Answer the question that was asked — not the adjacent one you find interesting

**What happened:** Asked "how does Project M resolve a tie when two characters attack at the same time with the same damage — is it random?", I filed #141 and researched whether two mirror CPU AIs could *parry indefinitely*. That's a real, nearby question — but it is not the one asked. The actual mechanic is **clank/priority** (simultaneous opposing hitboxes within a 9% damage window cancel; both fighters rebound; deterministic, no RNG). Worse: the answer was **already implemented in our own repo** — `CLANK_PRIORITY_RANGE = 9` in `config.py`, `_resolve_clanks()` in `systems/combat.py`, shipped by #133 three days earlier. I shipped an off-target writeup and *closed the ticket* before the reporter confirmed it.

**What I learned:** "Adjacent and interesting" feels like progress and reads like an answer, which is exactly why it's dangerous — a closed ticket buries the mismatch. Two cheap checks would have caught it: (a) re-read the literal question and map each claim in my answer back to a clause of it; (b) `grep` the codebase for the mechanic *before* reaching for SmashWiki — we often already model it.

**The rule:** **Before researching externally, grep the repo for the mechanic; before closing a research/question ticket, re-read the literal question and confirm the reporter is satisfied.** (Saved as the `confirm-before-close` memory; applied on #144 by holding the close until confirmation.)

---

## 2. Symmetric mechanics don't break a *perfect* mirror — a deterministic sim needs an explicit resolver

**What happened:** Reasoning about the mirror-loop (#141) and the randomness survey (#144), I first assumed "shields decay, so a stalemate self-resolves." Wrong in a true mirror: shield decay, clank, and hitstun are **symmetric** — both fighters' shields break on the same frame, both dizzy together, both recover together. The loop just gets a longer period. What actually resolves a real-PM mirror is **symmetry-breaking** (RNG in DI/CPU weighting; PM CPUs aren't frame-perfect) **plus the match timer** → sudden death.

**What I learned:** pycats is **deterministic by design — no RNG anywhere** (that's what makes replays and goldens reproducible). So unlike PM, *nothing in our engine breaks a symmetric standoff*. This reframed #61's `--vs` 30s/KO cap: it isn't a hack, it's the principled **analog of PM's match timer** — the only stalemate-breaker a no-RNG sim can have. PM itself is deterministic-*given-seed* (one PRNG stream; replays save only the seed); pycats is deterministic with no seed at all.

**The rule:** **In a deterministic sim, never expect a symmetric state to resolve emergently — add an explicit resolver (a clock/cap), and treat the engine's no-RNG determinism as a load-bearing invariant.** Any future randomness must be a single *seeded* PRNG threaded through the snapshot, never Python's global `random`.

---

## 3. A worktree is cut from main-at-claim-time — reconcile a suite failure against *current* origin/main before filing

**What happened:** Running the full suite in my #114 worktree, 5 combat tests were red (`AttributeError: 'SimpleNamespace' object has no attribute 'state'` at `combat.py:120`). I diagnosed the cause (a `defender.state` read added by #124 without a `getattr` guard) and was about to file a research spike. Before filing, I re-checked against current `origin/main` — and the failures were **already gone**: a sibling agent had filed and fixed them as #137 (`getattr(defender, "state", None)`) *during* my session. My worktree was simply based on an older `main` snapshot that predated the fix.

**What I learned:** In fleet mode, `pmtools claim` cuts your worktree from `main` at claim time, but other agents keep merging. A real-looking regression in your tree can be a fixed-upstream artifact of your stale base. Stashing my work and re-running confirmed the failures were *pre-existing on the base*, not mine — but "pre-existing" isn't the same as "still open."

**The rule:** **Before filing a regression you found in a worktree, reconcile it against current `origin/main` (and the open-issue list) — a stale base shows you bugs that are already fixed.** This is the active-state sibling of CHERRY's "the tracker moves under you" and my earlier "merged ≠ what your tree has."

---

## 4. pmtools close has two sharp edges — know the close path for the ticket's *shape*

**What happened:** Two distinct snags closing tickets this session:
- The **keyword guard** refused `pmtools close 141`: "no keyword from issue #141 title matched any unpushed commit subject." The title was the *original* framing ("mirror… parry indefinitely") while my commit subject was the *corrected* answer ("clank/priority… same-time trades"). `--skip-keyword-check` is the sanctioned path for a deliberately paraphrased / corrected-scope title.
- **No-code research tickets** (#141 first pass) have no `Closes #N` commit, so `pmtools close` can't run — close them via `gh issue close` + `pmtools release` (which clears the claim/worktree but leaves the issue's open/closed state to `gh`). When a research ticket *does* produce a committed doc (#144), the normal `Closes #N` + `pmtools close` works.

**What I learned:** The close mechanism depends on whether the deliverable is code/docs (commit-backed) or a comment (no commit), and the keyword guard assumes the title still describes the work. (Plus the known one: `pmtools close` exits 1 after success because it deletes its own cwd — trust the `CLOSE OK` banner.)

**The rule:** **Pick the close path up front: commit + `pmtools close` for code/doc deliverables; `gh issue close` + `pmtools release` for comment-only; `--skip-keyword-check` when the title was intentionally paraphrased.**

---

## 5. Extract a pure decision function out of the IO/CLI shell so the logic is testable

**What happened:** #61 needed `watch.py --vs` to run 30s-or-KO. Rather than bury the mode→duration logic inside `main()` next to argparse and the pygame presenter, I pulled it into `resolve_battle_plan(vs, match, frames) -> (frames, stop_on_match_over)`. That made the whole rule unit-testable without launching a window or encoding video, and `tests/test_watch_vs_duration.py` covers every mode + the `--frames` override. The override needed `argparse` `default=None` so "user passed `--frames 500`" is distinguishable from "user passed nothing (use the per-mode default)".

**What I learned:** The testability win is almost free — the decision is pure data-in/data-out; only the thin shell (argparse + `run_battle`) stays untested. `default=None` is the small trick that lets a pure resolver tell an explicit override from a default.

**The rule:** **Push branching logic out of the IO/CLI shell into a pure function the tests can call directly; use `argparse default=None` to distinguish an explicit override from the default.**

---

## 6. Throwaway verification artifacts go in the scratchpad — not a new top-level dir

**What happened:** To eyeball the #114 ASCII heads I rendered preview PNGs into a `repos/` directory in the worktree — a typo for the project's gitignored `repros/`. It showed up as untracked (`?? repos/`), so I had to `rm -rf` it before committing to avoid shipping stray binaries.

**What I learned:** The gitignored media dir is **`repros/`** (bug repros + media), and one-off visual checks don't belong in the repo at all — the session **scratchpad** is for that. A mistyped dir name silently isn't ignored.

**The rule:** **Render one-off verification artifacts into the session scratchpad; the repo's gitignored media dir is `repros/` (not `repos/`).**

---

## What landed

| Artifact | Change |
|---|---|
| `pycats/render_battle.py`, `entities/tail.py` | Whole-cat 50% flash from one `tinted()` source; tail colour into its cache key (#109) |
| `pycats/cat_faces.py` | Pure-ASCII profile/3-4 heads via a monospace block renderer; retired kaomoji/emoji styles (#114) |
| `watch.py` | `resolve_battle_plan()`: `--vs` runs 30s or until a 3-stock KO (#61) |
| `docs/research-findings-141-…md` | Clank/priority = the deterministic same-time-trade resolver (#141) |
| `docs/research-findings-144-…md` | PM randomness survey: deterministic fight math; RNG confined to specials/items/hazards/CPU; one seeded PRNG (#144) |

## Open threads

- **Authority path:** rules 1–6 here live only in narrative + the `confirm-before-close` memory. Candidates for `RULES.md` (didn't edit it to avoid a fleet collision on a shared file): the stale-worktree reconciliation check (#3) and the close-path-by-ticket-shape guidance (#4). File a docs ticket if these recur.
- A **seeded-PRNG seam** is the recommended future approach *if* a move-intrinsic-RNG character is ever authored (#144) — no ticket yet; not warranted until such a move exists.

## Related artifacts

- Prior: [TIL 2026-06-26 DRAGONFRUIT](./today-i-learned-2026-06-26-dragonfruit.md) (research deliverable = sourced ruling + only the follow-up it warrants)
- Issues #109, #114, #61, #141, #144; sibling fix #137; clank impl #133; match-cap #61
