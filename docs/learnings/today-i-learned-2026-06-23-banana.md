# TIL 2026-06-23 — BANANA

**Context:** Fixed two medium-severity physics defects in pycats — #5 (players jump
through the *side* faces of thick platforms) and #1 (players landing on each other
*lock* instead of pushing apart). Both turned into the same arc: reproduce as a
watchable sim, find the Project M reference behaviour, then fix at the physics layer
with TDD. This is the first entry in `docs/learnings/`.

---

## 1. Reproduce as a viewable sim *before* touching the fix

**What happened:** For both bugs I wrote a standalone driver (`repros/repro_issue_5.py`,
`repros/repro_issue_1.py`) that drives the *real* per-frame loop — `Player.update` +
the real `core.physics` resolvers + the real stage from `sim.runner.build_stage` —
seeds a deliberately bad starting state, prints a per-frame trajectory, and ends with a
plain-language **VERDICT**. Each supports `--live` (a real pygame window via
`LivePresenter`) and `--video` (an mp4 via `VideoPresenter`). I confirmed each visually
(extracting a still with imageio) before changing a line of game code.

**What I learned:** The driver doubles as a regression guard *for free* if you make its
exit code track the verdict (exit 0 while the bug is present, non-zero once fixed). The
"before" still (cat embedded in a wall; cat stuck on another cat's head) is far more
convincing than any prose, and the same script re-recorded "after" proves the fix.

**The rule:** **Every bug fix starts with a deterministic, viewable repro that drives the real loop and self-verifies.**

---

## 2. Collision geometry belongs in the physics layer, not the statechart

**What happened:** Both fixes landed in `pycats/core/physics.py`: #5 added
`solve_horizontal` (the horizontal sibling of `solve_vertical`), and #1 stripped
`resolve_player_push` down to X-axis-only. `Player.update` calls these for *both* state
backends, so one change fixed the live game, `watch.py`, and the headless runner at once.

**What I learned:** The statechart (`statecharts/fighter_chart.py`) governs *states*
(idle/jump/hurt), not pixel collision. The ticket for #1 said "use statecharts-py," but
putting wall-blocking or push-out into the chart would have braided geometry into the
state machine. Wall-jump / wall-cling / jostle-*strength* are genuine statechart work;
solid-wall blocking and X-push are not.

**The rule:** **Put collision geometry in `core/physics.py` (backend-agnostic); reserve the statechart for fighter *states*.**

---

## 3. Golden snapshots + parity are the oracle — and predictions about them lie

**What happened:** Both fixes ran the full README test suite, including
`tests/test_golden.py` (per-frame snapshot diff of three scripted battles) and
`tests/test_parity.py` (legacy vs statechart must be byte-identical). Neither fix shifted
a single golden, and parity held — so no `PYCATS_UPDATE_GOLDENS=1` regen was needed. For
#1 a planning subagent confidently predicted `combat.json` would shift "at frame 154";
the real golden test passed unchanged.

**What I learned:** A reasoned prediction about golden churn is a *hypothesis*, not a
result. The authoritative check is running `test_golden.py` + `test_parity.py` and reading
`git status tests/golden/`. Cheap, decisive, and it caught the subagent being wrong.

**The rule:** **Verify golden/parity impact by running the tests and diffing `tests/golden/` — never by prediction.**

---

## 4. Match-fidelity is the spec: find the Project M behaviour first

**What happened:** #5's "should" = thick platforms solid on all sides, thin platforms
one-way (so `solve_horizontal` skips `thin`). #1's "should" = Smash **jostle**: fighters
push apart **horizontally only**, with **no vertical pushbox** (you can briefly stand on a
head, then slide off sideways). I sourced jostle from SmashWiki and the repo's own
`docs/research/` notes before writing the X-only resolver.

**What I learned:** "Jostle" gave me the exact axis discipline the ticket wanted (ignore
Y, push X) and a name for the deferred refinement (gradual, per-character strength).
Naming the real mechanic turned a vague "push apart" into a testable spec.

**The rule:** **Before fixing a fighter mechanic, find and cite the Project M / Melee / Brawl reference; let it define the "should."**

---

## 5. Sequence tickets that touch the same file; don't parallelise them

**What happened:** #1 and #5 both edit `pycats/core/physics.py` (different functions:
`resolve_player_push` vs `solve_vertical`/`solve_horizontal`). My own orchestration pass
had called them "different surfaces" — wrong, same *file*. I landed #5 first (merged to
main), then claimed #1 off the updated main, so they never collided.

**What I learned:** Each ticket got its own `pmtools claim` worktree/branch, which is the
isolation mechanism — but isolation only prevents *edit-time* clobbering, not *merge-time*
conflicts. Same-file tickets still need ordering.

**The rule:** **Two tickets touching the same file get sequenced (land one, rebase the other) — separate worktrees are not a substitute for ordering.**

---

## 6. Treat subagent output as leads; confirm the load-bearing facts yourself

**What happened:** An Explore subagent reported wrong stage geometry (player start coords
off by ~200px); a Plan subagent predicted golden churn that never happened (lesson 3). I
re-derived geometry directly from `config.py` and ran the real tests.

**The rule:** **Subagent facts are leads — confirm anything load-bearing (coordinates, churn, call sites) first-hand.**

---

## What landed

| Artifact | Change |
|---|---|
| `pycats/core/physics.py` | Added `solve_horizontal` (solid side faces, #5); reduced `resolve_player_push` to X-only jostle (#1) |
| `tests/test_thick_platform_sides.py` | Side-face solidity + thin pass-through + top-landing (#5) |
| `tests/test_player_push.py` | Separate-on-X, settle-on-floor, never-touch-vel.y, dodge-skip, deterministic stacking (#1) |
| `repros/` (gitignored) | `repro_issue_5.py`, `repro_issue_1.py` self-verifying repro drivers |

## Open threads

- **Gradual / per-character "jostle strength"** (the PM refinement beyond X-only) — candidate research child under the #24 umbrella.
- **`repros/` is gitignored "for now"** — provisional; may later become tracked. Not yet codified in `RULES.md`.
- A stale claim ref `refs/claims/issue-25` surfaced during `pmtools claim` — worth a sweep.

## Related artifacts

- Issues #5, #1, #24 (research umbrella)
- [SmashWiki: Jostle](https://www.ssbwiki.com/Jostle)
